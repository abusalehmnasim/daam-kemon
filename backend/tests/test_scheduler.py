"""Tests for the stale-cleanup safety guard."""

from scrapers.scheduler import _stores_safe_to_prune


def test_only_healthy_stores_are_prunable():
    # shwapno scraped 0 (silently broke) -> must NOT be pruned.
    counts = {"chaldal": 500, "shwapno": 0, "daraz": 1200}
    assert _stores_safe_to_prune(counts) == {"chaldal", "daraz"}


def test_no_healthy_stores_prunes_nothing():
    # If every store scraped 0, prune nothing — never wipe the whole catalog.
    assert _stores_safe_to_prune({"shwapno": 0, "othoba": 0}) == set()
    assert _stores_safe_to_prune({}) == set()
