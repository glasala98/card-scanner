"""Tests for lookup_price game routing — mocks all network calls."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch, MagicMock
import scanner


MOCK_PRICE = {"price": 42.0, "price_label": "$42.00", "image_url": None}


def _mock_lookup(*args, **kwargs):
    return MOCK_PRICE


# ── Game routing ──────────────────────────────────────────────────────────────

def test_routes_nhl():
    with patch("modes.sports.lookup", side_effect=_mock_lookup):
        result = scanner.lookup_price("NHL", "Connor McDavid", "Young Guns", "2024-25")
    assert result["price"] == 42.0


def test_routes_nba():
    with patch("modes.sports.lookup", side_effect=_mock_lookup):
        result = scanner.lookup_price("NBA", "LeBron James", "Prizm", "2024")
    assert result["price"] == 42.0


def test_routes_nfl():
    with patch("modes.sports.lookup", side_effect=_mock_lookup):
        result = scanner.lookup_price("NFL", "Patrick Mahomes", "Optic", "2023")
    assert result["price"] == 42.0


def test_routes_mlb():
    with patch("modes.sports.lookup", side_effect=_mock_lookup):
        result = scanner.lookup_price("MLB", "Shohei Ohtani", "Topps", "2024")
    assert result["price"] == 42.0


def test_routes_pokemon():
    with patch("modes.pokemon.lookup", side_effect=_mock_lookup):
        result = scanner.lookup_price("Pokemon", "Charizard", "Base Set", "1999")
    assert result["price"] == 42.0


def test_routes_pokemon_accent():
    with patch("modes.pokemon.lookup", side_effect=_mock_lookup):
        result = scanner.lookup_price("Pokémon", "Pikachu", "Jungle", "1999")
    assert result["price"] == 42.0


def test_routes_mtg():
    with patch("modes.mtg.lookup", side_effect=_mock_lookup):
        result = scanner.lookup_price("MTG", "Black Lotus", "Alpha", "1993")
    assert result["price"] == 42.0


def test_routes_magic():
    with patch("modes.mtg.lookup", side_effect=_mock_lookup):
        result = scanner.lookup_price("Magic", "Mox Pearl", "Beta", "1993")
    assert result["price"] == 42.0


def test_routes_yugioh():
    with patch("modes.yugioh.lookup", side_effect=_mock_lookup):
        result = scanner.lookup_price("YuGiOh", "Blue-Eyes White Dragon", "", "2002")
    assert result["price"] == 42.0


def test_routes_yugioh_dash():
    with patch("modes.yugioh.lookup", side_effect=_mock_lookup):
        result = scanner.lookup_price("Yu-Gi-Oh", "Dark Magician", "", "2002")
    assert result["price"] == 42.0


def test_unknown_game_defaults_to_sports():
    with patch("modes.sports.lookup", side_effect=_mock_lookup):
        result = scanner.lookup_price("Unknown", "Mystery Card", "", "")
    assert result["price"] == 42.0


def test_empty_game_defaults_to_sports():
    with patch("modes.sports.lookup", side_effect=_mock_lookup):
        result = scanner.lookup_price("", "Some Card", "", "")
    assert result["price"] == 42.0


def test_lookup_error_returns_empty_dict():
    """If the mode module raises, lookup_price should return {} not crash."""
    with patch("modes.sports.lookup", side_effect=Exception("network error")):
        result = scanner.lookup_price("NHL", "Test", "", "")
    assert result == {}
