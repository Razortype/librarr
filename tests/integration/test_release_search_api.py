from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.core.exceptions import BookNotFoundError
from app.integrations.exceptions import (
    ProwlarrAuthError,
    ProwlarrNotConfiguredError,
    ProwlarrServerError,
    ProwlarrTimeoutError,
)
from app.schemas.release import ReleaseResult, ReleaseSearchResponse

_BOOK_ID = "00000000-0000-0000-0000-000000000001"

_HAPPY_RESPONSE = ReleaseSearchResponse(
    query="Test Book Test Author",
    results=[
        ReleaseResult(
            guid="abc123",
            title="Test Book.epub",
            indexer="MyIndexer",
            size_bytes=5_000_000,
            seeders=10,
            leechers=2,
            publish_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            download_url="https://example.com/dl",
            protocol="torrent",
            detected_format="epub",
            score=120,
        )
    ],
    total=1,
)

_PATCH_TARGET = "app.api.v1.book.release_search_service.search_releases"


# ---------------------------------------------------------------------------
# 200 — happy path
# ---------------------------------------------------------------------------


async def test_200_happy_path(api_client: httpx.AsyncClient) -> None:
    with patch(_PATCH_TARGET, AsyncMock(return_value=_HAPPY_RESPONSE)):
        r = await api_client.post(f"/api/v1/book/{_BOOK_ID}/release-search")

    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["query"] == "Test Book Test Author"
    assert body["results"][0]["detected_format"] == "epub"
    assert body["results"][0]["protocol"] == "torrent"
    assert "magnet_url" not in body["results"][0]


# ---------------------------------------------------------------------------
# 404 — book not found
# ---------------------------------------------------------------------------


async def test_404_book_not_found(api_client: httpx.AsyncClient) -> None:
    with patch(_PATCH_TARGET, AsyncMock(side_effect=BookNotFoundError(_BOOK_ID))):
        r = await api_client.post(f"/api/v1/book/{_BOOK_ID}/release-search")

    assert r.status_code == 404
    assert r.json()["details"]["book_id"] == _BOOK_ID


# ---------------------------------------------------------------------------
# 412 — Prowlarr not configured
# ---------------------------------------------------------------------------


async def test_412_prowlarr_not_configured(api_client: httpx.AsyncClient) -> None:
    with patch(_PATCH_TARGET, AsyncMock(side_effect=ProwlarrNotConfiguredError("not configured"))):
        r = await api_client.post(f"/api/v1/book/{_BOOK_ID}/release-search")

    assert r.status_code == 412
    assert "Prowlarr is not configured" in r.json()["detail"]


# ---------------------------------------------------------------------------
# 502 — Prowlarr auth error
# ---------------------------------------------------------------------------


async def test_502_auth_error(api_client: httpx.AsyncClient) -> None:
    with patch(_PATCH_TARGET, AsyncMock(side_effect=ProwlarrAuthError("bad key"))):
        r = await api_client.post(f"/api/v1/book/{_BOOK_ID}/release-search")

    assert r.status_code == 502
    assert "authentication" in r.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 504 — Prowlarr timeout
# ---------------------------------------------------------------------------


async def test_504_timeout(api_client: httpx.AsyncClient) -> None:
    with patch(_PATCH_TARGET, AsyncMock(side_effect=ProwlarrTimeoutError("timed out"))):
        r = await api_client.post(f"/api/v1/book/{_BOOK_ID}/release-search")

    assert r.status_code == 504


# ---------------------------------------------------------------------------
# 502 — Prowlarr server error
# ---------------------------------------------------------------------------


async def test_502_server_error(api_client: httpx.AsyncClient) -> None:
    with patch(
        _PATCH_TARGET,
        AsyncMock(side_effect=ProwlarrServerError(status_code=500, message="internal error")),
    ):
        r = await api_client.post(f"/api/v1/book/{_BOOK_ID}/release-search")

    assert r.status_code == 502
