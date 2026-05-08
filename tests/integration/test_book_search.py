from __future__ import annotations

import uuid
from datetime import UTC, datetime

import httpx

from app.integrations.exceptions import ProwlarrAuthError, ProwlarrTimeoutError
from app.schemas.prowlarr import ProwlarrRelease
from tests.conftest import MockProwlarrClient

_TITLE_PAYLOAD = {"lookup_type": "title_author", "title": "Dune"}


def _release(guid: str = "guid-1") -> ProwlarrRelease:
    return ProwlarrRelease(
        guid=guid,
        title=f"Release {guid}",
        indexer_name="TestIndexer",
        size_bytes=500_000,
        publish_date=datetime(2024, 1, 1, tzinfo=UTC),
        download_url=f"https://fake.test/dl/{guid}",
        info_url=None,
        seeders=5,
        leechers=1,
        protocol="torrent",
    )


async def test_search_releases_returns_results(
    api_client: httpx.AsyncClient,
    mock_prowlarr_client: MockProwlarrClient,
) -> None:
    r_add = await api_client.post("/api/v1/book", json=_TITLE_PAYLOAD)
    assert r_add.status_code == 201
    book_id = r_add.json()["book"]["id"]

    mock_prowlarr_client.search_results = [_release("guid-1")]

    r = await api_client.post(f"/api/v1/book/{book_id}/search")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1
    assert body[0]["guid"] == "guid-1"
    assert body[0]["indexer_name"] == "TestIndexer"
    assert body[0]["protocol"] == "torrent"
    assert body[0]["size_bytes"] == 500_000


async def test_search_releases_empty_results(
    api_client: httpx.AsyncClient,
    mock_prowlarr_client: MockProwlarrClient,
) -> None:
    r_add = await api_client.post("/api/v1/book", json=_TITLE_PAYLOAD)
    assert r_add.status_code == 201
    book_id = r_add.json()["book"]["id"]
    # mock_prowlarr_client.search_results defaults to []

    r = await api_client.post(f"/api/v1/book/{book_id}/search")
    assert r.status_code == 200
    assert r.json() == []


async def test_search_releases_book_not_found(
    api_client: httpx.AsyncClient,
) -> None:
    r = await api_client.post(f"/api/v1/book/{uuid.uuid4()}/search")
    assert r.status_code == 404
    assert r.json()["error"] == "not_found"


async def test_search_releases_query_includes_author(
    api_client: httpx.AsyncClient,
    mock_prowlarr_client: MockProwlarrClient,
) -> None:
    # Default mock metadata: title="Dune", author="Test Author"
    r_add = await api_client.post("/api/v1/book", json=_TITLE_PAYLOAD)
    assert r_add.status_code == 201
    book_id = r_add.json()["book"]["id"]

    await api_client.post(f"/api/v1/book/{book_id}/search")

    assert mock_prowlarr_client.last_query == "Dune Test Author"


async def test_search_releases_query_title_only_when_no_authors(
    api_client: httpx.AsyncClient,
    mock_prowlarr_client: MockProwlarrClient,
    mock_metadata_service: object,
) -> None:
    mock_metadata_service.search_not_found = True  # type: ignore[attr-defined]
    r_add = await api_client.post(
        "/api/v1/book", json={"lookup_type": "title_author", "title": "Orphan Book"}
    )
    assert r_add.status_code == 201
    book_id = r_add.json()["book"]["id"]

    await api_client.post(f"/api/v1/book/{book_id}/search")

    assert mock_prowlarr_client.last_query == "Orphan Book"


async def test_search_releases_prowlarr_timeout_returns_503(
    api_client: httpx.AsyncClient,
    mock_prowlarr_client: MockProwlarrClient,
) -> None:
    r_add = await api_client.post("/api/v1/book", json=_TITLE_PAYLOAD)
    assert r_add.status_code == 201
    book_id = r_add.json()["book"]["id"]

    mock_prowlarr_client.fail = ProwlarrTimeoutError("connection timed out")

    r = await api_client.post(f"/api/v1/book/{book_id}/search")
    assert r.status_code == 503
    assert r.json()["detail"] == "Prowlarr unreachable"


async def test_search_releases_prowlarr_auth_error_returns_502(
    api_client: httpx.AsyncClient,
    mock_prowlarr_client: MockProwlarrClient,
) -> None:
    r_add = await api_client.post("/api/v1/book", json=_TITLE_PAYLOAD)
    assert r_add.status_code == 201
    book_id = r_add.json()["book"]["id"]

    mock_prowlarr_client.fail = ProwlarrAuthError("invalid api key")

    r = await api_client.post(f"/api/v1/book/{book_id}/search")
    assert r.status_code == 502
    assert r.json()["detail"] == "Prowlarr authentication failed"
