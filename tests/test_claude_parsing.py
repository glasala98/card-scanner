"""Tests for Claude Vision response parsing in scan_frame."""

import sys
import os
import json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch, MagicMock
import scanner


def _make_frame():
    return np.zeros((480, 640, 3), dtype=np.uint8)


def _mock_response(text: str):
    msg = MagicMock()
    msg.content = [MagicMock(text=text)]
    return msg


def _patch_claude(text: str):
    return patch.object(scanner.client.messages, "create", return_value=_mock_response(text))


# ── Happy path ────────────────────────────────────────────────────────────────

def test_valid_card_detected():
    payload = json.dumps({
        "detected": True,
        "game": "NHL",
        "name": "Connor McDavid",
        "set": "Young Guns",
        "year": "2024-25",
        "variant": "RC",
        "confidence": 0.95,
    })
    with _patch_claude(payload):
        result = scanner.scan_frame(_make_frame())
    assert result["detected"] is True
    assert result["name"] == "Connor McDavid"
    assert result["confidence"] == 0.95


def test_no_card_detected():
    payload = json.dumps({"detected": False, "confidence": 0.0})
    with _patch_claude(payload):
        result = scanner.scan_frame(_make_frame())
    assert result["detected"] is False
    assert result["confidence"] == 0.0


def test_strips_markdown_code_fence():
    payload = "```json\n" + json.dumps({
        "detected": True,
        "game": "Pokemon",
        "name": "Charizard",
        "set": "Base Set",
        "year": "1999",
        "variant": "Holo",
        "confidence": 0.9,
    }) + "\n```"
    with _patch_claude(payload):
        result = scanner.scan_frame(_make_frame())
    assert result["detected"] is True
    assert result["name"] == "Charizard"


def test_strips_plain_code_fence():
    payload = "```\n" + json.dumps({
        "detected": True,
        "game": "MTG",
        "name": "Black Lotus",
        "set": "Alpha",
        "year": "1993",
        "variant": "Base",
        "confidence": 0.88,
    }) + "\n```"
    with _patch_claude(payload):
        result = scanner.scan_frame(_make_frame())
    assert result["name"] == "Black Lotus"


# ── Error handling ────────────────────────────────────────────────────────────

def test_invalid_json_returns_not_detected():
    with _patch_claude("Sorry, I can't identify this card."):
        result = scanner.scan_frame(_make_frame())
    assert result["detected"] is False
    assert result["confidence"] == 0.0


def test_claude_api_exception_returns_not_detected():
    with patch.object(scanner.client.messages, "create", side_effect=Exception("API error")):
        result = scanner.scan_frame(_make_frame())
    assert result["detected"] is False
    assert result["confidence"] == 0.0


def test_partial_response_survives():
    """Claude returning only some fields shouldn't crash."""
    payload = json.dumps({"detected": True, "confidence": 0.7})
    with _patch_claude(payload):
        result = scanner.scan_frame(_make_frame())
    assert result["detected"] is True
    assert result.get("name") is None
