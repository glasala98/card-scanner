"""
Scan a saved card image through Claude Vision + price lookup.
Use this to test the scanner with photos from your phone or saved images.

Usage:
    python scan_image.py path/to/card.jpg
    python scan_image.py path/to/card.jpg --game pokemon
    python scan_image.py path/to/card.jpg --json

Options:
    --game   Force a game type (sports/pokemon/mtg/yugioh). Skips Claude detection.
    --json   Print raw JSON output instead of formatted summary.
"""

import argparse
import json
import os
import sys
import base64

from dotenv import load_dotenv
load_dotenv()

from PIL import Image
from io import BytesIO


def load_image_b64(path: str) -> str:
    img = Image.open(path).convert("RGB")
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.standard_b64encode(buf.getvalue()).decode()


def identify_with_claude(img_b64: str) -> dict:
    import anthropic
    from scanner import CLAUDE_PROMPT, client
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
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def main():
    parser = argparse.ArgumentParser(description="Scan a card image file.")
    parser.add_argument("image", help="Path to card image (jpg/png/webp)")
    parser.add_argument("--game", help="Force game type: sports/pokemon/mtg/yugioh")
    parser.add_argument("--json", dest="as_json", action="store_true", help="Print raw JSON")
    args = parser.parse_args()

    if not os.path.exists(args.image):
        print(f"ERROR: File not found: {args.image}")
        sys.exit(1)

    print(f"Loading image: {args.image}")
    img_b64 = load_image_b64(args.image)

    if args.game:
        # Skip Claude, use forced game type
        result = {
            "detected": True,
            "game": args.game,
            "name": "?",
            "set": "",
            "year": "",
            "variant": "",
            "confidence": 1.0,
        }
        print(f"Game forced to: {args.game} (skipping Claude Vision)")
        # Still need a name — use Claude just for identification
        print("Identifying card name with Claude Vision...")
        try:
            claude_result = identify_with_claude(img_b64)
            result.update({k: v for k, v in claude_result.items() if k != "game"})
        except Exception as e:
            print(f"  Claude error: {e}")
    else:
        print("Identifying card with Claude Vision...")
        try:
            result = identify_with_claude(img_b64)
        except Exception as e:
            print(f"ERROR: Claude Vision failed: {e}")
            sys.exit(1)

    if args.as_json:
        print(json.dumps(result, indent=2))
        return

    # ── Pretty print identification ───────────────────────────────────────────
    print()
    print("=" * 50)
    print("  CARD IDENTIFIED")
    print("=" * 50)
    if not result.get("detected"):
        print("  No card detected in image.")
        print(f"  Confidence: {result.get('confidence', 0):.0%}")
        return

    print(f"  Game:       {result.get('game', 'Unknown')}")
    print(f"  Name:       {result.get('name', '?')}")
    print(f"  Set:        {result.get('set', '?')}")
    print(f"  Year:       {result.get('year', '?')}")
    print(f"  Variant:    {result.get('variant', 'Base')}")
    print(f"  Confidence: {result.get('confidence', 0):.0%}")
    print()

    # ── Price lookup ──────────────────────────────────────────────────────────
    print("Looking up price...")
    from scanner import lookup_price
    price_data = lookup_price(
        result.get("game", ""),
        result.get("name", ""),
        result.get("set", ""),
        result.get("year", ""),
    )

    print("=" * 50)
    print("  PRICE RESULT")
    print("=" * 50)
    print(f"  Price:      {price_data.get('price_label', 'No data')}")
    if price_data.get("price"):
        print(f"  Raw value:  ${price_data['price']:.2f}")
    if price_data.get("image_url"):
        print(f"  Image URL:  {price_data['image_url']}")
    print("=" * 50)

    if args.as_json:
        print(json.dumps({**result, **price_data}, indent=2))


if __name__ == "__main__":
    main()
