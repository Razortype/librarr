from __future__ import annotations

import json

import httpx
import pytest

from app.integrations.exceptions import (
    ProwlarrAuthError,
    ProwlarrNotFoundError,
    ProwlarrRateLimitError,
    ProwlarrServerError,
    ProwlarrTimeoutError,
)
from app.integrations.prowlarr.client import ProwlarrClient
from app.schemas.prowlarr import ProwlarrHealth, ProwlarrRelease
from tests.conftest import load_fixture


def make_mock_transport(
    status_code: int,
    body: dict | list | str,
    headers: dict[str, str] | None = None,
) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        content = json.dumps(body) if isinstance(body, (dict, list)) else body
        return httpx.Response(status_code, content=content.encode(), headers=headers or {})

    return httpx.MockTransport(handler)


def make_prowlarr_client(
    status_code: int = 200,
    body: dict | list | str = "",
    headers: dict[str, str] | None = None,
) -> ProwlarrClient:
    http = httpx.AsyncClient(
        transport=make_mock_transport(status_code, body, headers),
        base_url="http://prowlarr.test",
    )
    return ProwlarrClient(http, api_key="test-key")


# ---------------------------------------------------------------------------
# search()
# ---------------------------------------------------------------------------


async def test_search_returns_normalized_releases() -> None:
    fixture = load_fixture("prowlarr/search_response.json")
    client = make_prowlarr_client(body=fixture)

    releases = await client.search("project hail mary")

    assert len(releases) == len(fixture)
    assert isinstance(releases[0], ProwlarrRelease)
    assert releases[0].indexer_name == fixture[0]["indexer"]
    assert releases[0].size_bytes == fixture[0]["size"]


async def test_search_passes_query_params() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(dict(request.url.params))
        return httpx.Response(200, content=b"[]")

    http = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="http://prowlarr.test"
    )
    client = ProwlarrClient(http, api_key="k")

    await client.search("andy weir", limit=10)

    assert captured.get("query") == "andy weir"
    assert captured.get("type") == "search"
    assert captured.get("limit") == "10"


async def test_search_returns_empty_on_no_results() -> None:
    client = make_prowlarr_client(body=[])

    assert await client.search("nothing matches") == []


async def test_search_handles_usenet_release_with_null_fields() -> None:
    fixture = load_fixture("prowlarr/search_response.json")
    client = make_prowlarr_client(body=fixture)

    releases = await client.search("project hail mary")

    usenet = releases[1]
    assert usenet.protocol == "usenet"
    assert usenet.seeders is None
    assert usenet.leechers is None
    assert usenet.info_url is None


# ---------------------------------------------------------------------------
# health()
# ---------------------------------------------------------------------------


async def test_health_returns_normalized_status() -> None:
    fixture = load_fixture("prowlarr/health_response.json")
    client = make_prowlarr_client(body=fixture)

    health = await client.health()

    assert isinstance(health, ProwlarrHealth)
    assert health.version == fixture["version"]
    assert health.app_name == fixture["appName"]


# ---------------------------------------------------------------------------
# error translation
# ---------------------------------------------------------------------------


async def test_401_raises_auth_error() -> None:
    client = make_prowlarr_client(status_code=401, body={"error": "unauthorized"})

    with pytest.raises(ProwlarrAuthError):
        await client.search("q")


async def test_404_raises_not_found() -> None:
    client = make_prowlarr_client(status_code=404, body={"error": "not found"})

    with pytest.raises(ProwlarrNotFoundError):
        await client.search("q")


async def test_429_raises_rate_limit_with_retry_after() -> None:
    client = make_prowlarr_client(
        status_code=429,
        body={"error": "too many requests"},
        headers={"Retry-After": "30"},
    )

    with pytest.raises(ProwlarrRateLimitError) as exc_info:
        await client.search("q")

    assert exc_info.value.retry_after == 30


async def test_500_raises_server_error_after_retries() -> None:
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(500, content=b'{"error": "internal"}')

    http = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="http://prowlarr.test"
    )
    client = ProwlarrClient(http, api_key="k")

    with pytest.raises(ProwlarrServerError):
        await client.search("q")

    assert call_count == 3


async def test_timeout_raises_timeout_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("connection timed out")

    http = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="http://prowlarr.test"
    )
    client = ProwlarrClient(http, api_key="k")

    with pytest.raises(ProwlarrTimeoutError):
        await client.search("q")
