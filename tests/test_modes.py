"""Tests for price lookup modes — all network calls mocked."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch, MagicMock
import pytest


def _mock_response(json_data, status_code=200):
    r = MagicMock()
    r.status_code = status_code
    r.json.return_value = json_data
    r.raise_for_status = MagicMock()
    if status_code >= 400:
        r.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
    return r


# ── Sports (CardDB) ───────────────────────────────────────────────────────────

class TestSports:
    def test_returns_price_on_match(self):
        from modes import sports
        mock_resp = _mock_response([{"fair_value": 75.50, "image_url": "http://img/1.jpg"}])
        with patch("modes.sports.requests.get", return_value=mock_resp):
            result = sports.lookup("Connor McDavid", "Young Guns", "2024")
        assert result["price"] == 75.50
        assert result["price_label"] == "$75.50"

    def test_returns_no_price_on_empty(self):
        from modes import sports
        with patch("modes.sports.requests.get", return_value=_mock_response([])):
            result = sports.lookup("Unknown Player", "", "")
        assert result["price"] is None
        assert result["price_label"] == "No price data"

    def test_returns_no_price_when_fair_value_missing(self):
        from modes import sports
        with patch("modes.sports.requests.get", return_value=_mock_response([{"fair_value": None}])):
            result = sports.lookup("Test", "", "")
        assert result["price"] is None

    def test_lookup_error_on_exception(self):
        from modes import sports
        with patch("modes.sports.requests.get", side_effect=Exception("timeout")):
            result = sports.lookup("Test", "", "")
        assert result["price"] is None
        assert result["price_label"] == "Lookup error"


# ── Pokémon ───────────────────────────────────────────────────────────────────

class TestPokemon:
    def _card(self, prices):
        return {"data": [{"tcgplayer": {"prices": prices}, "images": {"small": "http://img/pika.jpg"}}]}

    def test_returns_holofoil_price(self):
        from modes import pokemon
        prices = {"holofoil": {"market": 120.0, "mid": 115.0}}
        with patch("modes.pokemon.requests.get", return_value=_mock_response(self._card(prices))):
            result = pokemon.lookup("Charizard", "Base Set", "1999")
        assert result["price"] == 120.0

    def test_falls_back_to_normal(self):
        from modes import pokemon
        prices = {"normal": {"market": 5.0}}
        with patch("modes.pokemon.requests.get", return_value=_mock_response(self._card(prices))):
            result = pokemon.lookup("Pikachu", "Base Set", "1999")
        assert result["price"] == 5.0

    def test_falls_back_to_mid_when_no_market(self):
        from modes import pokemon
        prices = {"holofoil": {"market": None, "mid": 80.0}}
        with patch("modes.pokemon.requests.get", return_value=_mock_response(self._card(prices))):
            result = pokemon.lookup("Blastoise", "Base Set", "1999")
        assert result["price"] == 80.0

    def test_no_cards_returns_no_data(self):
        from modes import pokemon
        with patch("modes.pokemon.requests.get", return_value=_mock_response({"data": []})):
            result = pokemon.lookup("Fake", "", "")
        assert result["price"] is None

    def test_exception_returns_lookup_error(self):
        from modes import pokemon
        with patch("modes.pokemon.requests.get", side_effect=Exception("timeout")):
            result = pokemon.lookup("Pikachu", "", "")
        assert result["price_label"] == "Lookup error"


# ── Magic: The Gathering ──────────────────────────────────────────────────────

class TestMTG:
    def _card(self, usd=None, usd_foil=None):
        return {
            "prices": {"usd": usd, "usd_foil": usd_foil},
            "image_uris": {"small": "http://img/lotus.jpg"},
        }

    def test_returns_usd_price(self):
        from modes import mtg
        with patch("modes.mtg.requests.get", return_value=_mock_response(self._card(usd="250.00"))):
            result = mtg.lookup("Black Lotus", "Alpha", "1993")
        assert result["price"] == 250.0

    def test_falls_back_to_foil(self):
        from modes import mtg
        with patch("modes.mtg.requests.get", return_value=_mock_response(self._card(usd=None, usd_foil="30.00"))):
            result = mtg.lookup("Forest", "Alpha", "1993")
        assert result["price"] == 30.0

    def test_no_price_returns_no_data(self):
        from modes import mtg
        with patch("modes.mtg.requests.get", return_value=_mock_response(self._card())):
            result = mtg.lookup("Rare Card", "", "")
        assert result["price"] is None
        assert result["price_label"] == "No price data"

    def test_exception_returns_lookup_error(self):
        from modes import mtg
        with patch("modes.mtg.requests.get", side_effect=Exception("404")):
            result = mtg.lookup("Unknown", "", "")
        assert result["price_label"] == "Lookup error"


# ── Yu-Gi-Oh ──────────────────────────────────────────────────────────────────

class TestYuGiOh:
    def _card(self, tcg_price="15.00"):
        return {
            "data": [{
                "card_prices": [{"tcgplayer_price": tcg_price}],
                "card_images": [{"image_url_small": "http://img/bewd.jpg"}],
            }]
        }

    def test_returns_tcgplayer_price(self):
        from modes import yugioh
        with patch("modes.yugioh.requests.get", return_value=_mock_response(self._card("25.00"))):
            result = yugioh.lookup("Blue-Eyes White Dragon", "", "2002")
        assert result["price"] == 25.0
        assert result["price_label"] == "$25.00"

    def test_zero_price_returns_no_data(self):
        from modes import yugioh
        with patch("modes.yugioh.requests.get", return_value=_mock_response(self._card("0.00"))):
            result = yugioh.lookup("Common Card", "", "")
        assert result["price"] is None

    def test_no_data_returns_no_price(self):
        from modes import yugioh
        with patch("modes.yugioh.requests.get", return_value=_mock_response({"data": []})):
            result = yugioh.lookup("Fake Card", "", "")
        assert result["price"] is None

    def test_exception_returns_lookup_error(self):
        from modes import yugioh
        with patch("modes.yugioh.requests.get", side_effect=Exception("timeout")):
            result = yugioh.lookup("Dark Magician", "", "")
        assert result["price_label"] == "Lookup error"
