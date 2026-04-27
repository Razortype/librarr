from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.edition import Edition


class EditionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get_by_isbn(self, isbn: str) -> Edition | None:
        col = Edition.isbn_13 if len(isbn) == 13 else Edition.isbn_10
        stmt = select(Edition).where(col == isbn).limit(1)
        return (await self._s.execute(stmt)).scalar_one_or_none()

    async def list_by_book(self, book_id: uuid.UUID) -> list[Edition]:
        stmt = select(Edition).where(Edition.book_id == book_id)
        return list((await self._s.execute(stmt)).scalars().all())

    async def create(
        self,
        *,
        book_id: uuid.UUID,
        isbn_10: str | None = None,
        isbn_13: str | None = None,
        asin: str | None = None,
        format: str | None = None,
        language: str | None = None,
        publisher: str | None = None,
        publication_date: date | None = None,
        page_count: int | None = None,
        audio_duration_seconds: int | None = None,
        narrators: list[str] | None = None,
        translators: list[str] | None = None,
        cover_url: str | None = None,
        external_ids: dict[str, str] | None = None,
        system_confidence: float = 0.0,
    ) -> Edition:
        edition = Edition(
            book_id=book_id,
            isbn_10=isbn_10,
            isbn_13=isbn_13,
            asin=asin,
            format=format,
            language=language,
            publisher=publisher,
            publication_date=publication_date,
            page_count=page_count,
            audio_duration_seconds=audio_duration_seconds,
            narrators=narrators,
            translators=translators,
            cover_url=cover_url,
            external_ids=external_ids or {},
            system_confidence=system_confidence,
        )
        self._s.add(edition)
        await self._s.flush()
        await self._s.refresh(edition)
        return edition
