"""Tests for the Flask overlay server endpoints."""

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import scanner
import server


@pytest.fixture
def client():
    server.app.config["TESTING"] = True
    with server.app.test_client() as c:
        yield c


def _set_state(**kwargs):
    with scanner._state_lock:
        scanner.current_card.update(kwargs)


def _reset_state():
    with scanner._state_lock:
        scanner.current_card.update({
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
        })


# ── /overlay ──────────────────────────────────────────────────────────────────

def test_overlay_returns_200(client):
    resp = client.get("/overlay")
    assert resp.status_code == 200


def test_overlay_contains_poll_script(client):
    resp = client.get("/overlay")
    assert b"poll()" in resp.data


def test_overlay_content_type_html(client):
    resp = client.get("/overlay")
    assert "text/html" in resp.content_type


# ── /api/current-card ─────────────────────────────────────────────────────────

def test_api_no_card_detected(client):
    _reset_state()
    resp = client.get("/api/current-card")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["detected"] is False


def test_api_card_detected(client):
    _set_state(
        detected=True,
        name="Connor McDavid",
        game="NHL",
        set="Young Guns",
        year="2024-25",
        price=142.0,
        price_label="$142.00",
        confidence=0.95,
        detected_at=time.time(),
    )
    resp = client.get("/api/current-card")
    data = resp.get_json()
    assert data["detected"] is True
    assert data["name"] == "Connor McDavid"
    assert data["price_label"] == "$142.00"
    _reset_state()


def test_api_includes_display_seconds(client):
    resp = client.get("/api/current-card")
    data = resp.get_json()
    assert "display_seconds" in data
    assert isinstance(data["display_seconds"], (int, float))


def test_api_response_is_json(client):
    resp = client.get("/api/current-card")
    assert resp.content_type == "application/json"


def test_api_state_isolation(client):
    """Two sequential requests should reflect updated state independently."""
    _reset_state()
    r1 = client.get("/api/current-card").get_json()
    assert r1["detected"] is False

    _set_state(detected=True, name="Charizard", game="Pokemon", price=300.0,
               price_label="$300.00", detected_at=time.time())
    r2 = client.get("/api/current-card").get_json()
    assert r2["detected"] is True
    assert r2["name"] == "Charizard"
    _reset_state()
