"""
Card Scanner — main loop
------------------------
Captures webcam frames, detects motion, sends to Claude Vision,
looks up price, and pushes result to the overlay server.

Run alongside server.py:
    python server.py &
    python scanner.py
"""

import os
import cv2
import time
import json
import base64
import threading
import numpy as np
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
import anthropic

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
with open(os.path.join(os.path.dirname(__file__), "config.json")) as f:
    CONFIG = json.load(f)

WEBCAM_INDEX       = CONFIG["webcam_index"]
MOTION_THRESHOLD   = CONFIG["motion_threshold"]
SCAN_COOLDOWN      = CONFIG["scan_cooldown_seconds"]
CACHE_TTL          = CONFIG["cache_ttl_seconds"]
CONFIDENCE_MIN     = CONFIG["claude_confidence_threshold"]

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# Shared state written by scanner, read by server
_state_lock = threading.Lock()
current_card = {
    "detected": False,
    "name": None,
    "set": None,
    "year": None,
    "game": None,
    "price": None,
    "price_label": None,
    "image_url": None,
    "confidence": None,
    "detected_at": None,
}

# ── Mode loader ───────────────────────────────────────────────────────────────
def lookup_price(game: str, name: str, set_name: str, year: str) -> dict:
    """Route to the correct price mode based on game type."""
    game = (game or "").lower()
    try:
        if any(s in game for s in ["nhl", "nba", "nfl", "mlb", "sports", "hockey", "basketball", "football", "baseball"]):
            from modes.sports import lookup
        elif "pokemon" in game or "pokémon" in game:
            from modes.pokemon import lookup
        elif "magic" in game or "mtg" in game:
            from modes.mtg import lookup
        elif "yugioh" in game or "yu-gi-oh" in game:
            from modes.yugioh import lookup
        else:
            from modes.sports import lookup  # default
        return lookup(name, set_name, year)
    except Exception as e:
        print(f"  Price lookup error: {e}")
        return {}


# ── Claude Vision ─────────────────────────────────────────────────────────────
CLAUDE_PROMPT = """You are a trading card expert. Identify the trading card in this image.

Return a JSON object with these fields:
{
  "detected": true/false,
  "game": "NHL/NBA/NFL/MLB/Pokemon/MTG/YuGiOh/Unknown",
  "name": "player or card name",
  "set": "set name",
  "year": "year or season e.g. 2024-25",
  "variant": "RC/Auto/Patch/Base/etc",
  "confidence": 0.0-1.0
}

If no card is clearly visible, return {"detected": false, "confidence": 0.0}.
Return only valid JSON, no other text."""


def scan_frame(frame) -> dict:
    """Send a frame to Claude Vision and return parsed card info."""
    # Encode frame as JPEG
    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    img_b64 = base64.standard_b64encode(buf.getvalue()).decode()

    try:
        msg = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=256,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img_b64}},
                    {"type": "text", "text": CLAUDE_PROMPT},
                ]
            }]
        )
        raw = msg.content[0].text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        print(f"  Claude error: {e}")
        return {"detected": False, "confidence": 0.0}


# ── Motion detection ──────────────────────────────────────────────────────────
def frames_differ(f1, f2, threshold=25) -> bool:
    """Return True if frames differ enough to suggest a new card appeared."""
    if f1 is None or f2 is None:
        return True
    gray1 = cv2.cvtColor(f1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(f2, cv2.COLOR_BGR2GRAY)
    diff  = cv2.absdiff(gray1, gray2)
    score = np.mean(diff)
    return score > threshold


# ── Cache ─────────────────────────────────────────────────────────────────────
_cache = {}  # key: card name → (result_dict, timestamp)

def cache_get(name: str):
    entry = _cache.get(name)
    if entry and (time.time() - entry[1]) < CACHE_TTL:
        return entry[0]
    return None

def cache_set(name: str, data: dict):
    _cache[name] = (data, time.time())


# ── Main loop ─────────────────────────────────────────────────────────────────
def update_state(data: dict):
    with _state_lock:
        current_card.update(data)
        current_card["detected_at"] = time.time()


def main():
    cap = cv2.VideoCapture(WEBCAM_INDEX)
    if not cap.isOpened():
        print(f"ERROR: Could not open webcam {WEBCAM_INDEX}")
        return

    print(f"Scanner started — webcam {WEBCAM_INDEX}")
    print("Hold a card up to the camera. Press Q to quit.\n")

    prev_frame   = None
    last_scan_at = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.1)
            continue

        # Show local preview window
        cv2.imshow("Card Scanner (Q to quit)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        now = time.time()

        # Rate limit: don't scan more than once per cooldown period
        if now - last_scan_at < SCAN_COOLDOWN:
            prev_frame = frame
            continue

        # Only scan if frame changed significantly
        if not frames_differ(prev_frame, frame, MOTION_THRESHOLD):
            prev_frame = frame
            continue

        prev_frame   = frame
        last_scan_at = now

        print("Motion detected — scanning...", end="", flush=True)
        result = scan_frame(frame)
        confidence = result.get("confidence", 0.0)

        if not result.get("detected") or confidence < CONFIDENCE_MIN:
            print(f" no card ({confidence:.0%} confidence)")
            update_state({"detected": False})
            continue

        name = result.get("name", "Unknown")
        print(f" {name} ({confidence:.0%})")

        # Check cache
        cached = cache_get(name)
        if cached:
            print(f"  [cached] {cached.get('price_label', '')}")
            update_state({**result, **cached, "detected": True})
            continue

        # Price lookup
        price_data = lookup_price(
            result.get("game", ""),
            name,
            result.get("set", ""),
            result.get("year", ""),
        )
        cache_set(name, price_data)

        label = price_data.get("price_label", "Price unavailable")
        print(f"  {label}")

        update_state({**result, **price_data, "detected": True})

    cap.release()
    cv2.destroyAllWindows()
    print("Scanner stopped.")


if __name__ == "__main__":
    main()
