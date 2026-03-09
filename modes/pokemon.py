"""Pokémon TCG — price lookup via pokemontcg.io."""

import requests


def lookup(name: str, set_name: str, year: str) -> dict:
    try:
        query = f'name:"{name}"'
        if set_name:
            query += f' set.name:"{set_name}"'

        r = requests.get(
            "https://api.pokemontcg.io/v2/cards",
            params={"q": query, "pageSize": 1, "orderBy": "-set.releaseDate"},
            timeout=5,
        )
        r.raise_for_status()
        cards = r.json().get("data", [])

        if not cards:
            return {"price_label": "No price data", "price": None}

        card = cards[0]
        prices = card.get("tcgplayer", {}).get("prices", {})

        # Try holofoil → normal → first available
        for ptype in ["holofoil", "normal", "reverseHolofoil", "1stEditionHolofoil"]:
            if ptype in prices:
                market = prices[ptype].get("market") or prices[ptype].get("mid")
                if market:
                    return {
                        "price": market,
                        "price_label": f"${market:.2f}",
                        "image_url": card.get("images", {}).get("small"),
                    }

        return {"price_label": "No price data", "price": None}

    except Exception:
        return {"price_label": "Lookup error", "price": None}
