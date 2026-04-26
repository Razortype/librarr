from __future__ import annotations

import json

import httpx
import pytest

from app.integrations.exceptions import OLNotFoundError, OLServerError
from app.integrations.openlibrary.client import OpenLibraryClient
from app.schemas.metadata import BookMetadata, EditionMetadata
from tests.conftest import load_fixture


def make_mock_transport(status_code: int, body: dict | str) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        content = json.dumps(body) if isinstance(body, dict) else body
        return httpx.Response(status_code, content=content.encode())

    return httpx.MockTransport(handler)


def make_ol_client(status_code: int, body: dict | str) -> OpenLibraryClient:
    http_client = httpx.AsyncClient(
        transport=make_mock_transport(status_code, body),
        base_url="https://openlibrary.org",
    )
    return OpenLibraryClient(http_client)


async def test_search_books_returns_normalized_results() -> None:
    fixture = load_fixture("openlibrary/search_response.json")
    client = make_ol_client(200, fixture)

    results = await client.search_books("The Left Hand of Darkness")

    assert len(results) == 2
    first = results[0]
    assert isinstance(first, BookMetadata)
    assert first.title == "The Left Hand of Darkness"
    assert first.ol_work_id == "OL45804W"
    assert first.system_confidence == 0.6
    assert first.cover_url is not None
    assert first.cover_url.startswith("https://covers.openlibrary.org")


async def test_search_books_author_stub_populated() -> None:
    fixture = load_fixture("openlibrary/search_response.json")
    client = make_ol_client(200, fixture)

    results = await client.search_books("The Left Hand of Darkness")

    assert results[0].authors[0].name == "Ursula K. Le Guin"
    assert results[0].authors[0].ol_id == "OL26320A"


async def test_lookup_author_normalizes_biography() -> None:
    fixture = load_fixture("openlibrary/author_response.json")
    client = make_ol_client(200, fixture)

    author = await client.lookup_author("OL26320A")

    assert author.biography == "Ursula Kroeber Le Guin was an American author."
    assert author.birth_year == 1929
    assert author.death_year == 2018
    assert author.image_url is not None
    assert author.image_url.startswith("https://covers.openlibrary.org/a/id/")


async def test_lookup_by_isbn_returns_edition() -> None:
    fixture = load_fixture("openlibrary/edition_response.json")
    client = make_ol_client(200, fixture)

    edition = await client.lookup_by_isbn("9780441478125")

    assert isinstance(edition, EditionMetadata)
    assert edition.isbn_13 == "9780441478125"
    assert edition.language == "en"
    assert edition.format == "paperback"
    assert edition.publisher == "Ace Books"


async def test_search_books_5xx_raises_ol_server_error() -> None:
    client = make_ol_client(500, {"error": "internal server error"})

    with pytest.raises(OLServerError):
        await client.search_books("anything")


async def test_lookup_by_isbn_404_raises_ol_not_found() -> None:
    client = make_ol_client(404, {"error": "not found"})

    with pytest.raises(OLNotFoundError):
        await client.lookup_by_isbn("9780000000000")
