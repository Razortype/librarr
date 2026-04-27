from __future__ import annotations

import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.author import Author

logger = structlog.get_logger(__name__)


class AuthorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get(self, author_id: uuid.UUID) -> Author | None:
        return await self._s.get(Author, author_id)

    async def get_by_external_id(self, source: str, value: str) -> Author | None:
        """Match on external_ids JSON key. Checks: openlibrary, goodreads, isni, wikidata."""
        # SQLite / Postgres JSON path: external_ids->>'key' == value
        # SQLAlchemy JSON column supports [] operator for key access
        stmt = select(Author).where(
            Author.external_ids[source].as_string() == value
        )
        return (await self._s.execute(stmt)).scalar_one_or_none()

    async def get_by_name(
        self, canonical_name: str, birth_year: int | None = None
    ) -> Author | None:
        """Name-based dedup fallback. Logs a warning — collision risk."""
        stmt = select(Author).where(Author.canonical_name == canonical_name)
        if birth_year is not None:
            stmt = stmt.where(Author.birth_year == birth_year)

        result = (await self._s.execute(stmt)).scalar_one_or_none()
        if result is not None:
            logger.warning(
                "author_dedup_by_name",
                canonical_name=canonical_name,
                birth_year=birth_year,
                author_id=str(result.id),
                reason="no_external_id_match",
            )
        return result

    async def create(
        self,
        *,
        canonical_name: str,
        sort_name: str,
        aliases: list[str] | None = None,
        birth_year: int | None = None,
        death_year: int | None = None,
        biography: str | None = None,
        image_url: str | None = None,
        external_ids: dict[str, str] | None = None,
        system_confidence: float = 0.0,
    ) -> Author:
        author = Author(
            canonical_name=canonical_name,
            sort_name=sort_name,
            aliases=aliases or [],
            birth_year=birth_year,
            death_year=death_year,
            biography=biography,
            image_url=image_url,
            external_ids=external_ids or {},
            system_confidence=system_confidence,
        )
        self._s.add(author)
        await self._s.flush()
        await self._s.refresh(author)
        return author

    async def merge_external_ids(
        self, author: Author, new_ids: dict[str, str]
    ) -> None:
        """Merge new external IDs into existing without overwriting present ones."""
        merged = {**new_ids, **author.external_ids}
        if merged != author.external_ids:
            author.external_ids = merged
            await self._s.flush()
