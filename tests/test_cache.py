"""Tests for the in-memory card cache."""

import time
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import scanner


def setup_function():
    """Clear cache before each test."""
    scanner._cache.clear()


def test_cache_miss_returns_none():
    assert scanner.cache_get("Connor McDavid") is None


def test_cache_hit_returns_data():
    data = {"price": 50.0, "price_label": "$50.00"}
    scanner.cache_set("Connor McDavid", data)
    assert scanner.cache_get("Connor McDavid") == data


def test_cache_different_keys_isolated():
    scanner.cache_set("Card A", {"price": 10.0})
    scanner.cache_set("Card B", {"price": 20.0})
    assert scanner.cache_get("Card A")["price"] == 10.0
    assert scanner.cache_get("Card B")["price"] == 20.0


def test_cache_overwrite():
    scanner.cache_set("Card A", {"price": 10.0})
    scanner.cache_set("Card A", {"price": 99.0})
    assert scanner.cache_get("Card A")["price"] == 99.0


def test_cache_expires_after_ttl(monkeypatch):
    """Entry should be stale once TTL has elapsed."""
    monkeypatch.setattr(scanner, "CACHE_TTL", 0.1)
    scanner.cache_set("Old Card", {"price": 5.0})
    time.sleep(0.15)
    assert scanner.cache_get("Old Card") is None


def test_cache_valid_before_ttl(monkeypatch):
    monkeypatch.setattr(scanner, "CACHE_TTL", 60)
    scanner.cache_set("Fresh Card", {"price": 5.0})
    assert scanner.cache_get("Fresh Card") is not None
