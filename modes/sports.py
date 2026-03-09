"""Sports cards — price lookup via CardDB API."""

import requests
import json
import os

with open(os.path.join(os.path.dirname(__file__), "..", "config.json")) as f:
    _cfg = json.load(f)

BASE_URL = _cfg.get("carddb_api_url", "https://southwestsportscards.ca/api")


def lookup(name: str, set_name: str, year: str) -> dict:
    try:
        params = {"search": name, "limit": 5}
        if year:
            params["year"] = year
        r = requests.get(f"{BASE_URL}/catalog", params=params, timeout=5)
        r.raise_for_status()
        cards = r.json()

        if not cards:
            return {"price_label": "No price data", "price": None}

        # Pick best match
        card = cards[0]
        price = card.get("fair_value")
        if price:
            return {
                "price": price,
                "price_label": f"${price:.2f}",
                "image_url": card.get("image_url"),
            }
        return {"price_label": "No price data", "price": None}

    except Exception as e:
        return {"price_label": "Lookup error", "price": None}
