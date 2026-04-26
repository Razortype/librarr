from __future__ import annotations

import httpx
import pytest

from app.core.config import settings
from app.integrations.openlibrary.client import OpenLibraryClient
from app.schemas.metadata import BookMetadata


@pytest.mark.network
async def test_ol_search_returns_results() -> None:
    """Smoke test: hit the real Open Library API and verify we get normalized results."""
    timeout = httpx.Timeout(
        connect=settings.http_timeout_connect,
        read=settings.http_timeout_read,
        write=5.0,
        pool=5.0,
    )
    async with httpx.AsyncClient(base_url=settings.openlibrary_base_url, timeout=timeout) as http:
        client = OpenLibraryClient(http)
        results = await client.search_books(title="The Left Hand of Darkness", author="Le Guin")

    assert len(results) > 0
    first = results[0]
    assert isinstance(first, BookMetadata)
    assert first.title
    assert first.system_confidence == 0.6
    assert first.ol_work_id is not None
