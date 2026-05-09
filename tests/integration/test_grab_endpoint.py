from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx

from app.core.exceptions import BookNotFoundError
from app.integrations.exceptions import (
    ProwlarrDownloadError,
    QBittorrentAddError,
    QBittorrentHashLookupError,
    QBittorrentNotConfiguredError,
)
from app.schemas.grab import GrabStatus

_BOOK_ID = "00000000-0000-0000-0000-000000000001"
_GRAB_ID = "00000000-0000-0000-0000-000000000002"
_HASH = "a" * 40
_PATCH_TARGET = "app.api.v1.book.grab_service.grab"

_MOCK_GRAB = SimpleNamespace(
    id=uuid.UUID(_GRAB_ID),
    book_id=uuid.UUID(_BOOK_ID),
    release_title="Great Book EPUB",
    indexer_name="MyIndexer",
    size_bytes=5_000_000,
    qbit_hash=_HASH,
    status=GrabStatus.GRABBED,
    grabbed_at=datetime(2026, 1, 1, tzinfo=UTC),
)

_REQUEST_BODY = {
    "release_guid": "abc123",
    "release_data": {
        "guid": "abc123",
        "title": "Great Book EPUB",
        "indexer": "MyIndexer",
        "size_bytes": 5_000_000,
        "seeders": 10,
        "leechers": 2,
        "publish_date": "2025-01-01T00:00:00Z",
        "download_url": "https://prowlarr.local/dl/abc",
        "protocol": "torrent",
        "detected_format": "epub",
        "score": 120,
    },
}


# ---------------------------------------------------------------------------
# 200 — happy path
# ---------------------------------------------------------------------------


async def test_200_happy_path(api_client: httpx.AsyncClient) -> None:
    with patch(_PATCH_TARGET, AsyncMock(return_value=_MOCK_GRAB)):
        r = await api_client.post(f"/api/v1/book/{_BOOK_ID}/grab", json=_REQUEST_BODY)

    assert r.status_code == 200
    body = r.json()
    assert body["id"] == _GRAB_ID
    assert body["book_id"] == _BOOK_ID
    assert body["qbit_hash"] == _HASH
    assert body["release_title"] == "Great Book EPUB"
    assert body["indexer_name"] == "MyIndexer"
    assert body["size_bytes"] == 5_000_000
    assert body["status"] == "grabbed"


# ---------------------------------------------------------------------------
# 404 — book not found
# ---------------------------------------------------------------------------


async def test_404_book_not_found(api_client: httpx.AsyncClient) -> None:
    with patch(_PATCH_TARGET, AsyncMock(side_effect=BookNotFoundError(_BOOK_ID))):
        r = await api_client.post(f"/api/v1/book/{_BOOK_ID}/grab", json=_REQUEST_BODY)

    assert r.status_code == 404
    assert r.json()["details"]["book_id"] == _BOOK_ID


# ---------------------------------------------------------------------------
# 200 — duplicate grab returns existing (idempotent)
# ---------------------------------------------------------------------------


async def test_200_duplicate_returns_existing(api_client: httpx.AsyncClient) -> None:
    with patch(_PATCH_TARGET, AsyncMock(return_value=_MOCK_GRAB)):
        r1 = await api_client.post(f"/api/v1/book/{_BOOK_ID}/grab", json=_REQUEST_BODY)
        r2 = await api_client.post(f"/api/v1/book/{_BOOK_ID}/grab", json=_REQUEST_BODY)

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["id"] == r2.json()["id"]


# ---------------------------------------------------------------------------
# 422 — malformed request body
# ---------------------------------------------------------------------------


async def test_422_malformed_body(api_client: httpx.AsyncClient) -> None:
    r = await api_client.post(
        f"/api/v1/book/{_BOOK_ID}/grab",
        json={"release_guid": "abc"},  # missing release_data
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# 502 — Prowlarr download error
# ---------------------------------------------------------------------------


async def test_502_prowlarr_download_error(api_client: httpx.AsyncClient) -> None:
    with patch(_PATCH_TARGET, AsyncMock(side_effect=ProwlarrDownloadError("500 from indexer"))):
        r = await api_client.post(f"/api/v1/book/{_BOOK_ID}/grab", json=_REQUEST_BODY)

    assert r.status_code == 502
    assert "Prowlarr download error" in r.json()["detail"]


# ---------------------------------------------------------------------------
# 502 — qBittorrent add error
# ---------------------------------------------------------------------------


async def test_502_qbittorrent_add_error(api_client: httpx.AsyncClient) -> None:
    with patch(_PATCH_TARGET, AsyncMock(side_effect=QBittorrentAddError("Fails."))):
        r = await api_client.post(f"/api/v1/book/{_BOOK_ID}/grab", json=_REQUEST_BODY)

    assert r.status_code == 502
    assert "qBittorrent error" in r.json()["detail"]


# ---------------------------------------------------------------------------
# 504 — hash lookup timed out
# ---------------------------------------------------------------------------


async def test_504_hash_lookup_timeout(api_client: httpx.AsyncClient) -> None:
    with patch(_PATCH_TARGET, AsyncMock(side_effect=QBittorrentHashLookupError("exhausted"))):
        r = await api_client.post(f"/api/v1/book/{_BOOK_ID}/grab", json=_REQUEST_BODY)

    assert r.status_code == 504
    assert "timed out" in r.json()["detail"]


# ---------------------------------------------------------------------------
# 412 — qBittorrent not configured
# ---------------------------------------------------------------------------


async def test_412_qbittorrent_not_configured(api_client: httpx.AsyncClient) -> None:
    with patch(
        _PATCH_TARGET,
        AsyncMock(side_effect=QBittorrentNotConfiguredError("not configured")),
    ):
        r = await api_client.post(f"/api/v1/book/{_BOOK_ID}/grab", json=_REQUEST_BODY)

    assert r.status_code == 412
    assert "qBittorrent" in r.json()["detail"]
