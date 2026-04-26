from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.exceptions import CloudTimeoutError
from app.schemas.metadata import AuthorMetadata, BookMetadata, EditionMetadata
from app.services.metadata import MetadataService


def _make_book_metadata(**kwargs: object) -> BookMetadata:
    defaults: dict[str, object] = {
        "ol_work_id": "OL45804W",
        "title": "The Left Hand of Darkness",
        "system_confidence": 0.95,
    }
    defaults.update(kwargs)
    return BookMetadata(**defaults)  # type: ignore[arg-type]


def _make_edition_metadata(**kwargs: object) -> EditionMetadata:
    defaults: dict[str, object] = {
        "ol_edition_id": "OL7353617M",
        "title": "The Left Hand of Darkness",
        "isbn_13": "9780441478125",
        "system_confidence": 0.92,
    }
    defaults.update(kwargs)
    return EditionMetadata(**defaults)  # type: ignore[arg-type]


def _make_author_metadata(**kwargs: object) -> AuthorMetadata:
    defaults: dict[str, object] = {
        "ol_id": "OL26320A",
        "name": "Ursula K. Le Guin",
        "system_confidence": 0.6,
    }
    defaults.update(kwargs)
    return AuthorMetadata(**defaults)  # type: ignore[arg-type]


async def test_search_books_skips_cloud_when_no_api_key() -> None:
    ol_client = MagicMock()
    cloud_client = MagicMock()

    book = _make_book_metadata()
    ol_client.search_books = AsyncMock(return_value=[book])
    cloud_client.enrich_request = AsyncMock()

    service = MetadataService(ol_client=ol_client, cloud_client=cloud_client)

    with patch("app.services.metadata.settings") as mock_settings:
        mock_settings.librarr_cloud_api_key = ""
        results = await service.search_books("The Left Hand of Darkness")

    ol_client.search_books.assert_called_once()
    cloud_client.enrich_request.assert_not_called()
    assert results == [book]


async def test_search_books_uses_cloud_when_api_key_set() -> None:
    ol_client = MagicMock()
    cloud_client = MagicMock()

    book = _make_book_metadata()

    # Cloud returns complete immediately
    from app.integrations.librarr_cloud.schemas import EnrichStatus

    complete_status = EnrichStatus(request_id="req-abc123", status="complete", result=book)
    cloud_client.enrich_request = AsyncMock(return_value=complete_status)
    ol_client.search_books = AsyncMock(return_value=[book])

    service = MetadataService(ol_client=ol_client, cloud_client=cloud_client)

    with patch("app.services.metadata.settings") as mock_settings:
        mock_settings.librarr_cloud_api_key = "test-key"
        results = await service.search_books("The Left Hand of Darkness")

    assert len(results) == 1
    assert results[0] is book


async def test_search_books_falls_back_on_cloud_timeout() -> None:
    ol_client = MagicMock()
    cloud_client = MagicMock()

    book = _make_book_metadata(system_confidence=0.6)
    cloud_client.enrich_request = AsyncMock(side_effect=CloudTimeoutError("timed out"))
    ol_client.search_books = AsyncMock(return_value=[book])

    service = MetadataService(ol_client=ol_client, cloud_client=cloud_client)

    with patch("app.services.metadata.settings") as mock_settings:
        mock_settings.librarr_cloud_api_key = "test-key"
        results = await service.search_books("The Left Hand of Darkness")

    ol_client.search_books.assert_called_once()
    assert results == [book]


async def test_lookup_by_isbn_returns_cloud_result() -> None:
    ol_client = MagicMock()
    cloud_client = MagicMock()

    edition = _make_edition_metadata()
    cloud_client.lookup = AsyncMock(return_value=edition)
    ol_client.lookup_by_isbn = AsyncMock()

    service = MetadataService(ol_client=ol_client, cloud_client=cloud_client)

    with patch("app.services.metadata.settings") as mock_settings:
        mock_settings.librarr_cloud_api_key = "test-key"
        result = await service.lookup_by_isbn("9780441478125")

    assert result is edition
    ol_client.lookup_by_isbn.assert_not_called()


async def test_lookup_by_isbn_falls_back_on_cloud_miss() -> None:
    ol_client = MagicMock()
    cloud_client = MagicMock()

    edition = _make_edition_metadata()
    cloud_client.lookup = AsyncMock(return_value=None)
    ol_client.lookup_by_isbn = AsyncMock(return_value=edition)

    service = MetadataService(ol_client=ol_client, cloud_client=cloud_client)

    with patch("app.services.metadata.settings") as mock_settings:
        mock_settings.librarr_cloud_api_key = "test-key"
        result = await service.lookup_by_isbn("9780441478125")

    ol_client.lookup_by_isbn.assert_called_once_with("9780441478125")
    assert result is edition


async def test_lookup_author_always_uses_ol() -> None:
    ol_client = MagicMock()
    cloud_client = MagicMock()

    author = _make_author_metadata()
    ol_client.lookup_author = AsyncMock(return_value=author)

    service = MetadataService(ol_client=ol_client, cloud_client=cloud_client)

    result = await service.lookup_author("OL26320A")

    ol_client.lookup_author.assert_called_once_with("OL26320A")
    # cloud_client has no async methods called — verify no interactions
    assert not cloud_client.method_calls
    assert result is author
