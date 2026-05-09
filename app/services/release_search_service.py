from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BookNotFoundError
from app.repositories.book import BookRepository
from app.schemas.release import ReleaseResult, ReleaseSearchResponse
from app.services import prowlarr_service
from app.services.release_scoring import score_release

_SEARCH_LIMIT = 100
_RESULT_CAP = 50
_MIN_SEEDERS = 1
_MIN_SIZE_BYTES = 100 * 1024  # 100 KB


async def search_releases(session: AsyncSession, book_id: uuid.UUID) -> ReleaseSearchResponse:
    books = BookRepository(session)
    book = await books.get(book_id)
    if book is None:
        raise BookNotFoundError(str(book_id))

    author_rows = await books.get_authors_for_book(book_id)
    primary_name = author_rows[0].author.canonical_name if author_rows else ""
    query = f"{book.title} {primary_name}".strip()

    async with prowlarr_service.get_active_client(session) as client:
        raw_releases = await client.search(query=query, limit=_SEARCH_LIMIT)

    results: list[ReleaseResult] = []
    for r in raw_releases:
        seeders = r.seeders or 0
        if seeders < _MIN_SEEDERS:
            continue
        if r.size_bytes < _MIN_SIZE_BYTES:
            continue
        if r.protocol != "torrent":
            continue

        detected_format, final_score = score_release(
            title=r.title,
            seeders=seeders,
            size_bytes=r.size_bytes,
            publish_date=r.publish_date,
        )

        results.append(
            ReleaseResult(
                guid=r.guid,
                title=r.title,
                indexer=r.indexer_name,
                size_bytes=r.size_bytes,
                seeders=seeders,
                leechers=r.leechers or 0,
                publish_date=r.publish_date,
                download_url=r.download_url,
                protocol="torrent",
                detected_format=detected_format,
                score=final_score,
            )
        )

    results.sort(key=lambda x: x.score, reverse=True)
    capped = results[:_RESULT_CAP]

    return ReleaseSearchResponse(query=query, results=capped, total=len(capped))
