from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BookNotFoundError
from app.integrations.exceptions import (
    ProwlarrDownloadError,
    QBittorrentAddError,
    QBittorrentError,
    QBittorrentHashLookupError,
)
from app.models.grab import Grab
from app.repositories.book import BookRepository
from app.schemas.grab import GrabRequest
from app.services import prowlarr_service, qbittorrent_service

_QBIT_CATEGORY = "librarr-ebook"
_HASH_POLL_ATTEMPTS = 5
_HASH_POLL_SLEEP = 1.0


async def grab(
    session: AsyncSession,
    book_id: uuid.UUID,
    request: GrabRequest,
) -> Grab:
    """Orchestrate manual grab: fetch release from Prowlarr, push to qBit, persist.

    Raises:
        BookNotFoundError: book_id not in DB.
        ProwlarrDownloadError: download_url fetch failed or release has no URL.
        QBittorrentAddError: qBit refused the torrent.
        QBittorrentHashLookupError: hash not found after add (polling exhausted).
    """
    book = await BookRepository(session).get(book_id)
    if book is None:
        raise BookNotFoundError(str(book_id))

    existing = await _get_existing(session, book_id, request.release_guid)
    if existing is not None:
        return existing

    if not request.release_data.download_url:
        raise ProwlarrDownloadError("release has no download_url")

    async with prowlarr_service.get_active_client(session) as prowlarr:
        download = await prowlarr.download_release(request.release_data.download_url)

    tag = f"book:{book_id}"
    tags_str = f"librarr,{tag}"

    async with qbittorrent_service.get_active_client(session) as qbit:
        try:
            if isinstance(download, bytes):
                await qbit.add_torrent_file(download, category=_QBIT_CATEGORY, tags=tags_str)
            else:
                await qbit.add_torrent(download, category=_QBIT_CATEGORY, tags=tags_str)
        except QBittorrentError as exc:
            raise QBittorrentAddError(str(exc)) from exc

        qbit_hash: str | None = None
        for _ in range(_HASH_POLL_ATTEMPTS):
            await asyncio.sleep(_HASH_POLL_SLEEP)
            torrents = await qbit.get_torrents(tag=tag)
            if torrents:
                qbit_hash = torrents[0]["hash"]
                break

        if qbit_hash is None:
            raise QBittorrentHashLookupError(
                f"Hash not found after {_HASH_POLL_ATTEMPTS} attempts for book {book_id}"
            )

    grab_record = Grab(
        book_id=book_id,
        release_guid=request.release_guid,
        release_title=request.release_data.title,
        indexer_name=request.release_data.indexer,
        size_bytes=request.release_data.size_bytes,
        qbit_hash=qbit_hash,
    )
    session.add(grab_record)
    book.status = "grabbed"
    await session.commit()
    await session.refresh(grab_record)
    return grab_record


async def _get_existing(
    session: AsyncSession, book_id: uuid.UUID, release_guid: str
) -> Grab | None:
    stmt = select(Grab).where(Grab.book_id == book_id, Grab.release_guid == release_guid)
    return (await session.execute(stmt)).scalar_one_or_none()
