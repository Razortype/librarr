from __future__ import annotations

import json

import httpx
import pytest

from app.integrations.exceptions import CloudServerError
from app.integrations.librarr_cloud.client import CloudClient
from app.schemas.metadata import BookMetadata, EditionMetadata
from tests.conftest import load_fixture


def make_mock_transport(status_code: int, body: dict | str) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        content = json.dumps(body) if isinstance(body, dict) else body
        return httpx.Response(status_code, content=content.encode())

    return httpx.MockTransport(handler)


def make_cloud_client(status_code: int, body: dict | str) -> CloudClient:
    http_client = httpx.AsyncClient(
        transport=make_mock_transport(status_code, body),
        base_url="https://api.librarr.com",
    )
    return CloudClient(http_client, api_key="test-key")


async def test_enrich_request_returns_pending_status() -> None:
    fixture = load_fixture("cloud/enrich_pending.json")
    client = make_cloud_client(200, fixture)

    status = await client.enrich_request(query="The Left Hand of Darkness", entity_type="book")

    assert status.status == "pending"
    assert status.request_id == "req-abc123"


async def test_enrich_poll_returns_complete_with_result() -> None:
    fixture = load_fixture("cloud/enrich_complete.json")
    client = make_cloud_client(200, fixture)

    status = await client.enrich_poll(request_id="req-abc123")

    assert status.status == "complete"
    assert status.result is not None
    assert isinstance(status.result, BookMetadata)
    assert status.result.title == "The Left Hand of Darkness"
    assert status.result.system_confidence == 0.95


async def test_lookup_returns_edition_on_hit() -> None:
    fixture = load_fixture("cloud/lookup_hit.json")
    client = make_cloud_client(200, fixture)

    result = await client.lookup(external_id="isbn:9780441478125", entity_type="edition")

    assert result is not None
    assert isinstance(result, EditionMetadata)
    assert result.isbn_13 == "9780441478125"


async def test_lookup_returns_none_on_miss() -> None:
    fixture = load_fixture("cloud/lookup_miss.json")
    client = make_cloud_client(200, fixture)

    result = await client.lookup(external_id="isbn:0000000000000", entity_type="edition")

    assert result is None


async def test_enrich_request_5xx_raises_cloud_server_error() -> None:
    client = make_cloud_client(500, {"error": "internal server error"})

    with pytest.raises(CloudServerError):
        await client.enrich_request(query="anything", entity_type="book")


async def test_feedback_swallows_errors() -> None:
    client = make_cloud_client(500, {"error": "internal server error"})

    # Must not raise — fire-and-forget
    await client.feedback(
        request_id="req-abc123",
        field="title",
        correct_value="The Left Hand of Darkness",
        entity_type="book",
    )
