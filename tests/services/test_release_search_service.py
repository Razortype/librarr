from __future__ import annotations

import contextlib
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BookNotFoundError
from app.integrations.exceptions import ProwlarrAuthError, ProwlarrNotConfiguredError
from app.integrations.prowlarr.client import ProwlarrClient
from app.models.associations import book_authors_table
from app.models.author import Author
from app.models.book import Book
from app.schemas.prowlarr import ProwlarrRelease
from app.services.release_search_service import search_releases

_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)

_BASE_RELEASE = ProwlarrRelease(
    guid="r1",
    title="Great Book EPUB",
    indexer_name="MyIndexer",
    size_bytes=5_000_000,
    publish_date=_NOW,
    download_url="https://example.com/dl",
    info_url=None,
    seeders=10,
    leechers=2,
    protocol="torrent",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _insert_book(
    session: AsyncSession,
    title: str,
    author_name: str | None = "Jane Doe",
) -> Book:
    book = Book(title=title, status="wanted", system_confidence=0.8)
    session.add(book)
    await session.flush()

    if author_name is not None:
        author = Author(canonical_name=author_name, sort_name=author_name, system_confidence=0.8)
        session.add(author)
        await session.flush()
        await session.execute(
            book_authors_table.insert().values(
                book_id=book.id,
                author_id=author.id,
                role="primary",
                position=1,
            )
        )
        await session.flush()

    return book


def _make_active_client_ctx(mock_client: ProwlarrClient) -> object:
    @contextlib.asynccontextmanager
    async def _ctx(session: AsyncSession) -> AsyncGenerator[ProwlarrClient]:
        yield mock_client

    return _ctx


def _make_raises_ctx(exc: Exception) -> object:
    @contextlib.asynccontextmanager
    async def _ctx(session: AsyncSession) -> AsyncGenerator[None]:
        raise exc
        yield  # type: ignore[misc]

    return _ctx


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


async def test_happy_path_returns_scored_results(db_session: AsyncSession) -> None:
    book = await _insert_book(db_session, "Great Book", "Jane Doe")
    mock_client = AsyncMock()
    mock_client.search = AsyncMock(return_value=[_BASE_RELEASE])

    with patch("app.services.prowlarr_service.get_active_client", _make_active_client_ctx(mock_client)):
        result = await search_releases(db_session, book.id)

    assert result.query == "Great Book Jane Doe"
    assert result.total == 1
    assert result.results[0].title == "Great Book EPUB"
    assert result.results[0].detected_format == "epub"
    assert result.results[0].indexer == "MyIndexer"
    assert result.results[0].protocol == "torrent"


async def test_query_uses_title_only_when_no_author(db_session: AsyncSession) -> None:
    book = await _insert_book(db_session, "Orphan Book", author_name=None)
    mock_client = AsyncMock()
    mock_client.search = AsyncMock(return_value=[])

    with patch("app.services.prowlarr_service.get_active_client", _make_active_client_ctx(mock_client)):
        result = await search_releases(db_session, book.id)

    assert result.query == "Orphan Book"
    mock_client.search.assert_awaited_once_with(query="Orphan Book", limit=100)


async def test_search_called_with_limit_100(db_session: AsyncSession) -> None:
    book = await _insert_book(db_session, "Book", "Author")
    mock_client = AsyncMock()
    mock_client.search = AsyncMock(return_value=[])

    with patch("app.services.prowlarr_service.get_active_client", _make_active_client_ctx(mock_client)):
        await search_releases(db_session, book.id)

    mock_client.search.assert_awaited_once_with(query="Book Author", limit=100)


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------


async def test_zero_seeder_release_filtered(db_session: AsyncSession) -> None:
    book = await _insert_book(db_session, "Book", "Author")
    zero_seed = _BASE_RELEASE.model_copy(update={"guid": "r_zero", "seeders": 0})
    mock_client = AsyncMock()
    mock_client.search = AsyncMock(return_value=[zero_seed])

    with patch("app.services.prowlarr_service.get_active_client", _make_active_client_ctx(mock_client)):
        result = await search_releases(db_session, book.id)

    assert result.total == 0


async def test_small_release_filtered(db_session: AsyncSession) -> None:
    book = await _insert_book(db_session, "Book", "Author")
    tiny = _BASE_RELEASE.model_copy(update={"guid": "r_tiny", "size_bytes": 1024})
    mock_client = AsyncMock()
    mock_client.search = AsyncMock(return_value=[tiny])

    with patch("app.services.prowlarr_service.get_active_client", _make_active_client_ctx(mock_client)):
        result = await search_releases(db_session, book.id)

    assert result.total == 0


async def test_usenet_release_filtered(db_session: AsyncSession) -> None:
    book = await _insert_book(db_session, "Book", "Author")
    usenet = _BASE_RELEASE.model_copy(update={"guid": "r_usenet", "protocol": "usenet"})
    mock_client = AsyncMock()
    mock_client.search = AsyncMock(return_value=[usenet])

    with patch("app.services.prowlarr_service.get_active_client", _make_active_client_ctx(mock_client)):
        result = await search_releases(db_session, book.id)

    assert result.total == 0


# ---------------------------------------------------------------------------
# Ordering
# ---------------------------------------------------------------------------


async def test_results_ordered_by_score_descending(db_session: AsyncSession) -> None:
    book = await _insert_book(db_session, "Book", "Author")
    low = _BASE_RELEASE.model_copy(update={"guid": "r_low", "seeders": 1})
    high = _BASE_RELEASE.model_copy(update={"guid": "r_high", "seeders": 50})
    mock_client = AsyncMock()
    mock_client.search = AsyncMock(return_value=[low, high])

    with patch("app.services.prowlarr_service.get_active_client", _make_active_client_ctx(mock_client)):
        result = await search_releases(db_session, book.id)

    assert result.total == 2
    assert result.results[0].guid == "r_high"
    assert result.results[0].score > result.results[1].score


# ---------------------------------------------------------------------------
# Empty results
# ---------------------------------------------------------------------------


async def test_empty_results_returned(db_session: AsyncSession) -> None:
    book = await _insert_book(db_session, "Book", "Author")
    mock_client = AsyncMock()
    mock_client.search = AsyncMock(return_value=[])

    with patch("app.services.prowlarr_service.get_active_client", _make_active_client_ctx(mock_client)):
        result = await search_releases(db_session, book.id)

    assert result.total == 0
    assert result.results == []


# ---------------------------------------------------------------------------
# Error propagation
# ---------------------------------------------------------------------------


async def test_book_not_found_raises(db_session: AsyncSession) -> None:
    with pytest.raises(BookNotFoundError):
        await search_releases(db_session, uuid.uuid4())


async def test_unconfigured_raises(db_session: AsyncSession) -> None:
    book = await _insert_book(db_session, "Book", "Author")

    with patch(
        "app.services.prowlarr_service.get_active_client",
        _make_raises_ctx(ProwlarrNotConfiguredError("not configured")),
    ):
        with pytest.raises(ProwlarrNotConfiguredError):
            await search_releases(db_session, book.id)


async def test_auth_error_propagates(db_session: AsyncSession) -> None:
    book = await _insert_book(db_session, "Book", "Author")
    mock_client = AsyncMock()
    mock_client.search = AsyncMock(side_effect=ProwlarrAuthError("bad key"))

    with patch("app.services.prowlarr_service.get_active_client", _make_active_client_ctx(mock_client)):
        with pytest.raises(ProwlarrAuthError):
            await search_releases(db_session, book.id)
