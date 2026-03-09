"""
Demo mode — cycles through one example card per game type in the OBS overlay.
No webcam or Anthropic API key needed.

Usage:
    python demo.py

Then open http://localhost:5050/overlay in a browser or OBS Browser Source.
Each card displays for ~5 seconds, then the next one loads.
"""

import time
import threading
import json
import os

# Load config before importing scanner so state is shared
with open(os.path.join(os.path.dirname(__file__), "config.json")) as f:
    _cfg = json.load(f)

import scanner
import server

# ── Example cards, one per supported game type ────────────────────────────────
DEMO_CARDS = [
    {
        "detected": True,
        "game": "NHL",
        "name": "Connor McDavid",
        "set": "Upper Deck Young Guns",
        "year": "2015-16",
        "variant": "RC",
        "price": 850.00,
        "price_label": "$850.00",
        "image_url": None,
        "confidence": 0.97,
    },
    {
        "detected": True,
        "game": "NBA",
        "name": "Victor Wembanyama",
        "set": "Panini Prizm",
        "year": "2023-24",
        "variant": "RC",
        "price": 120.00,
        "price_label": "$120.00",
        "image_url": None,
        "confidence": 0.95,
    },
    {
        "detected": True,
        "game": "NFL",
        "name": "Patrick Mahomes",
        "set": "Panini Optic",
        "year": "2017",
        "variant": "RC",
        "price": 210.00,
        "price_label": "$210.00",
        "image_url": None,
        "confidence": 0.93,
    },
    {
        "detected": True,
        "game": "MLB",
        "name": "Shohei Ohtani",
        "set": "Topps Chrome",
        "year": "2018",
        "variant": "RC",
        "price": 195.00,
        "price_label": "$195.00",
        "image_url": None,
        "confidence": 0.96,
    },
    {
        "detected": True,
        "game": "Pokemon",
        "name": "Charizard",
        "set": "Base Set",
        "year": "1999",
        "variant": "Holo",
        "price": 420.00,
        "price_label": "$420.00",
        "image_url": None,
        "confidence": 0.98,
    },
    {
        "detected": True,
        "game": "MTG",
        "name": "Black Lotus",
        "set": "Alpha",
        "year": "1993",
        "variant": "Base",
        "price": 40000.00,
        "price_label": "$40,000.00",
        "image_url": None,
        "confidence": 0.91,
    },
    {
        "detected": True,
        "game": "YuGiOh",
        "name": "Blue-Eyes White Dragon",
        "set": "Legend of Blue Eyes",
        "year": "2002",
        "variant": "1st Edition",
        "price": 850.00,
        "price_label": "$850.00",
        "image_url": None,
        "confidence": 0.94,
    },
    {
        "detected": False,
        "name": None,
        "game": None,
        "price": None,
        "price_label": None,
        "confidence": 0.0,
    },
]

DISPLAY_SECONDS = _cfg.get("overlay_display_seconds", 5)


def _cycle():
    """Inject each demo card into shared scanner state on a timer."""
    print(f"\nCycling through {len(DEMO_CARDS)} example cards ({DISPLAY_SECONDS}s each)...")
    print("Open http://localhost:5050/overlay in your browser or OBS.\n")
    i = 0
    while True:
        card = DEMO_CARDS[i % len(DEMO_CARDS)]
        scanner.update_state(card)
        label = card.get("price_label") or "(no card)"
        name  = card.get("name") or "---"
        game  = card.get("game") or ""
        print(f"  [{i % len(DEMO_CARDS) + 1}/{len(DEMO_CARDS)}] {game:8s}  {name:30s}  {label}")
        time.sleep(DISPLAY_SECONDS + 1)
        i += 1


if __name__ == "__main__":
    port = _cfg.get("overlay_port", 5050)
    print("=" * 55)
    print("  Card Scanner — Demo Mode")
    print("=" * 55)
    print(f"  Overlay URL:  http://localhost:{port}/overlay")
    print(f"  API URL:      http://localhost:{port}/api/current-card")
    print("=" * 55)

    t = threading.Thread(target=_cycle, daemon=True)
    t.start()

    server.app.run(host="0.0.0.0", port=port, debug=False)
