from __future__ import annotations


def make_cache_key(source: str, raw_id: str) -> str:
    """Returns a namespaced cache key, e.g. 'openlibrary:OL123W'."""
    if not source or not raw_id:
        raise ValueError("source and raw_id must be non-empty")
    return f"{source}:{raw_id}"
