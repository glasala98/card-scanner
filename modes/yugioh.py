"""Yu-Gi-Oh — price lookup via YGOPRODeck API."""

import requests


def lookup(name: str, set_name: str, year: str) -> dict:
    try:
        r = requests.get(
            "https://db.ygoprodeck.com/api/v7/cardinfo.php",
            params={"name": name, "tcgplayer_data": "true"},
            timeout=5,
        )
        r.raise_for_status()
        data = r.json().get("data", [])

        if not data:
            return {"price_label": "No price data", "price": None}

        card = data[0]
        prices = card.get("card_prices", [{}])[0]
        tcg = prices.get("tcgplayer_price")
        if tcg and float(tcg) > 0:
            return {
                "price": float(tcg),
                "price_label": f"${float(tcg):.2f}",
                "image_url": card.get("card_images", [{}])[0].get("image_url_small"),
            }
        return {"price_label": "No price data", "price": None}

    except Exception:
        return {"price_label": "Lookup error", "price": None}
