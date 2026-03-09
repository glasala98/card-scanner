"""Magic: The Gathering — price lookup via Scryfall API."""

import requests


def lookup(name: str, set_name: str, year: str) -> dict:
    try:
        params = {"fuzzy": name}
        if set_name:
            params["set"] = set_name[:3].lower()  # Scryfall uses 3-letter set codes

        r = requests.get("https://api.scryfall.com/cards/named", params=params, timeout=5)
        r.raise_for_status()
        card = r.json()

        prices = card.get("prices", {})
        usd = prices.get("usd") or prices.get("usd_foil")
        if usd:
            return {
                "price": float(usd),
                "price_label": f"${float(usd):.2f}",
                "image_url": card.get("image_uris", {}).get("small"),
            }
        return {"price_label": "No price data", "price": None}

    except Exception:
        return {"price_label": "Lookup error", "price": None}
