from __future__ import annotations

import contextlib
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BookNotFoundError
from app.integrations.exceptions import (
    ProwlarrDownloadError,
    QBittorrentAddError,
    QBittorrentError,
    QBittorrentHashLookupError,
)
from app.models.book import Book
from app.models.grab import Grab
from app.schemas.grab import GrabRequest
from app.schemas.release import ReleaseResult
from app.services import grab_service

_NOW = datetime(2026, 1, 1, tzinfo=UTC)
_FAKE_HASH = "a" * 40

_PROWLARR_CTX = "app.services.grab_service.prowlarr_service.get_active_client"
_QBIT_CTX = "app.services.grab_service.qbittorrent_service.get_active_client"
_SLEEP = "asyncio.sleep"


def _make_release(download_url: str | None = "https://prowlarr.local/dl/abc") -> ReleaseResult:
    return ReleaseResult(
        guid="release-guid-1",
        title="Great Book EPUB",
        indexer="MyIndexer",
        size_bytes=5_000_000,
        seeders=10,
        leechers=2,
        publish_date=_NOW,
        download_url=download_url,
        protocol="torrent",
        detected_format="epub",
        score=120,
    )


def _make_request(release: ReleaseResult | None = None) -> GrabRequest:
    return GrabRequest(
        release_guid="release-guid-1",
        release_data=release or _make_release(),
    )


async def _insert_book(session: AsyncSession) -> Book:
    book = Book(title="Great Book", status="wanted", system_confidence=0.8)
    session.add(book)
    await session.flush()
    return book


# ---------------------------------------------------------------------------
# Context-manager helpers
# ---------------------------------------------------------------------------


def _make_ctx(mock_client: object) -> object:
    @contextlib.asynccontextmanager
    async def _ctx(session: AsyncSession) -> AsyncGenerator[object]:
        yield mock_client

    return _ctx


def _prowlarr_bytes(content: bytes = b"torrent-content") -> object:
    mock = AsyncMock()
    mock.download_release = AsyncMock(return_value=content)
    return mock


def _prowlarr_magnet(magnet: str = "magnet:?xt=urn:btih:abc123") -> object:
    mock = AsyncMock()
    mock.download_release = AsyncMock(return_value=magnet)
    return mock


def _qbit_happy(qbit_hash: str = _FAKE_HASH) -> object:
    mock = AsyncMock()
    mock.add_torrent = AsyncMock(return_value=None)
    mock.add_torrent_file = AsyncMock(return_value=None)
    mock.get_torrents = AsyncMock(return_value=[{"hash": qbit_hash}])
    return mock


# ---------------------------------------------------------------------------
# Happy path — .torrent bytes
# ---------------------------------------------------------------------------


async def test_happy_path_torrent_bytes(db_session: AsyncSession) -> None:
    book = await _insert_book(db_session)
    prowlarr_mock = _prowlarr_bytes()
    qbit_mock = _qbit_happy()

    with (
        patch(_PROWLARR_CTX, _make_ctx(prowlarr_mock)),
        patch(_QBIT_CTX, _make_ctx(qbit_mock)),
        patch(_SLEEP, AsyncMock()),
    ):
        result = await grab_service.grab(db_session, book.id, _make_request())

    assert isinstance(result, Grab)
    assert str(result.book_id) == str(book.id)
    assert result.qbit_hash == _FAKE_HASH
    assert result.release_guid == "release-guid-1"
    qbit_mock.add_torrent_file.assert_awaited_once()
    qbit_mock.add_torrent.assert_not_awaited()


# ---------------------------------------------------------------------------
# Happy path — magnet redirect
# ---------------------------------------------------------------------------


async def test_happy_path_magnet(db_session: AsyncSession) -> None:
    book = await _insert_book(db_session)
    prowlarr_mock = _prowlarr_magnet()
    qbit_mock = _qbit_happy()

    with (
        patch(_PROWLARR_CTX, _make_ctx(prowlarr_mock)),
        patch(_QBIT_CTX, _make_ctx(qbit_mock)),
        patch(_SLEEP, AsyncMock()),
    ):
        result = await grab_service.grab(db_session, book.id, _make_request())

    assert result.qbit_hash == _FAKE_HASH
    qbit_mock.add_torrent.assert_awaited_once()
    qbit_mock.add_torrent_file.assert_not_awaited()


# ---------------------------------------------------------------------------
# Idempotency — duplicate returns existing, no re-add
# ---------------------------------------------------------------------------


async def test_duplicate_returns_existing_no_readd(db_session: AsyncSession) -> None:
    book = await _insert_book(db_session)
    prowlarr_mock = _prowlarr_bytes()
    qbit_mock = _qbit_happy()

    with (
        patch(_PROWLARR_CTX, _make_ctx(prowlarr_mock)),
        patch(_QBIT_CTX, _make_ctx(qbit_mock)),
        patch(_SLEEP, AsyncMock()),
    ):
        first = await grab_service.grab(db_session, book.id, _make_request())
        second = await grab_service.grab(db_session, book.id, _make_request())

    assert first.id == second.id
    assert qbit_mock.add_torrent_file.await_count == 1


# ---------------------------------------------------------------------------
# Book not found
# ---------------------------------------------------------------------------


async def test_book_not_found_raises(db_session: AsyncSession) -> None:
    with pytest.raises(BookNotFoundError):
        await grab_service.grab(db_session, uuid.uuid4(), _make_request())


# ---------------------------------------------------------------------------
# Prowlarr download returns error → ProwlarrDownloadError propagates
# ---------------------------------------------------------------------------


async def test_prowlarr_download_error_propagates(db_session: AsyncSession) -> None:
    book = await _insert_book(db_session)
    prowlarr_mock = AsyncMock()
    prowlarr_mock.download_release = AsyncMock(
        side_effect=ProwlarrDownloadError("500 from indexer")
    )

    with (
        patch(_PROWLARR_CTX, _make_ctx(prowlarr_mock)),
        pytest.raises(ProwlarrDownloadError),
    ):
        await grab_service.grab(db_session, book.id, _make_request())


# ---------------------------------------------------------------------------
# No download_url → ProwlarrDownloadError
# ---------------------------------------------------------------------------


async def test_no_download_url_raises(db_session: AsyncSession) -> None:
    book = await _insert_book(db_session)
    request = _make_request(_make_release(download_url=None))

    with pytest.raises(ProwlarrDownloadError):
        await grab_service.grab(db_session, book.id, request)


# ---------------------------------------------------------------------------
# qBit add fails → QBittorrentAddError, no Grab persisted
# ---------------------------------------------------------------------------


async def test_qbit_add_fails_no_record(db_session: AsyncSession) -> None:
    book = await _insert_book(db_session)
    prowlarr_mock = _prowlarr_bytes()
    qbit_mock = AsyncMock()
    qbit_mock.add_torrent_file = AsyncMock(side_effect=QBittorrentError("Fails."))
    qbit_mock.get_torrents = AsyncMock(return_value=[])

    with (
        patch(_PROWLARR_CTX, _make_ctx(prowlarr_mock)),
        patch(_QBIT_CTX, _make_ctx(qbit_mock)),
        pytest.raises(QBittorrentAddError),
    ):
        await grab_service.grab(db_session, book.id, _make_request())

    rows = (
        await db_session.execute(select(Grab).where(Grab.book_id == book.id))
    ).scalars().all()
    assert rows == []


# ---------------------------------------------------------------------------
# Hash polling exhausted → QBittorrentHashLookupError, no Grab persisted
# ---------------------------------------------------------------------------


async def test_hash_poll_exhausted_no_record(db_session: AsyncSession) -> None:
    book = await _insert_book(db_session)
    prowlarr_mock = _prowlarr_bytes()
    qbit_mock = AsyncMock()
    qbit_mock.add_torrent_file = AsyncMock(return_value=None)
    qbit_mock.get_torrents = AsyncMock(return_value=[])

    with (
        patch(_PROWLARR_CTX, _make_ctx(prowlarr_mock)),
        patch(_QBIT_CTX, _make_ctx(qbit_mock)),
        patch(_SLEEP, AsyncMock()),
        pytest.raises(QBittorrentHashLookupError),
    ):
        await grab_service.grab(db_session, book.id, _make_request())

    rows = (
        await db_session.execute(select(Grab).where(Grab.book_id == book.id))
    ).scalars().all()
    assert rows == []


# ---------------------------------------------------------------------------
# Grab record fields match input snapshot
# ---------------------------------------------------------------------------


async def test_grab_record_snapshot_fields(db_session: AsyncSession) -> None:
    book = await _insert_book(db_session)
    prowlarr_mock = _prowlarr_bytes()
    qbit_mock = _qbit_happy("b" * 40)

    with (
        patch(_PROWLARR_CTX, _make_ctx(prowlarr_mock)),
        patch(_QBIT_CTX, _make_ctx(qbit_mock)),
        patch(_SLEEP, AsyncMock()),
    ):
        result = await grab_service.grab(db_session, book.id, _make_request())

    assert result.release_title == "Great Book EPUB"
    assert result.indexer_name == "MyIndexer"
    assert result.size_bytes == 5_000_000
    assert result.qbit_hash == "b" * 40
    assert result.release_guid == "release-guid-1"


# ---------------------------------------------------------------------------
# book.status set to 'grabbed' after successful grab
# ---------------------------------------------------------------------------


async def test_book_status_set_to_grabbed(db_session: AsyncSession) -> None:
    book = await _insert_book(db_session)
    prowlarr_mock = _prowlarr_bytes()
    qbit_mock = _qbit_happy()

    with (
        patch(_PROWLARR_CTX, _make_ctx(prowlarr_mock)),
        patch(_QBIT_CTX, _make_ctx(qbit_mock)),
        patch(_SLEEP, AsyncMock()),
    ):
        await grab_service.grab(db_session, book.id, _make_request())

    await db_session.refresh(book)
    assert book.status == "grabbed"
