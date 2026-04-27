from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.associations import book_authors_table
from app.models.author import Author
from app.models.book import Book
from app.models.edition import Edition
from app.models.series import Series


@dataclass
class AuthorWithRole:
    author: Author
    role: str
    position: int | None


@dataclass
class BookListRow:
    book: Book
    primary_author: Author | None
    cover_url: str | None


_SORT_COLUMNS: dict[str, Any] = {
    "title": Book.title,
    "publication_year": Book.publication_year,
    "added_at": Book.created_at,
    "effective_confidence": Book.effective_confidence,
}


class BookRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    async def list(
        self,
        *,
        status: str | None = None,
        author_id: uuid.UUID | None = None,
        series_id: uuid.UUID | None = None,
        monitored: bool | None = None,
        sort_key: str = "title",
        sort_dir: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[BookListRow], int]:
        stmt = select(Book).options(
            selectinload(Book.editions),
        )

        stmt = self._apply_filters(stmt, status=status, author_id=author_id,
                                   series_id=series_id, monitored=monitored)
        stmt = self._apply_sort(stmt, sort_key=sort_key, sort_dir=sort_dir,
                                author_id_filter=author_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total: int = (await self._s.execute(count_stmt)).scalar_one()

        stmt = stmt.offset(offset).limit(limit)
        books = list((await self._s.execute(stmt)).scalars().all())

        primary_authors = await self._load_primary_authors({b.id for b in books})

        rows: list[BookListRow] = []
        for book in books:
            cover = next((e.cover_url for e in book.editions if e.cover_url), None)
            rows.append(BookListRow(
                book=book,
                primary_author=primary_authors.get(book.id),
                cover_url=cover,
            ))

        return rows, total

    async def get(self, book_id: uuid.UUID) -> Book | None:
        stmt = (
            select(Book)
            .where(Book.id == book_id)
            .options(
                selectinload(Book.editions),
                selectinload(Book.series),
            )
            .execution_options(populate_existing=True)
        )
        return (await self._s.execute(stmt)).scalar_one_or_none()

    async def get_authors_for_book(self, book_id: uuid.UUID) -> list[AuthorWithRole]:
        stmt = (
            select(Author, book_authors_table.c.role, book_authors_table.c.position)
            .join(book_authors_table, Author.id == book_authors_table.c.author_id)
            .where(book_authors_table.c.book_id == book_id)
            .order_by(book_authors_table.c.position.asc().nulls_last())
        )
        rows = (await self._s.execute(stmt)).all()
        return [AuthorWithRole(author=r[0], role=r[1], position=r[2]) for r in rows]

    async def get_by_isbn(self, isbn: str) -> Book | None:
        """Return the book linked to an edition with this ISBN (10 or 13)."""
        col = Edition.isbn_13 if len(isbn) == 13 else Edition.isbn_10
        stmt = (
            select(Book)
            .join(Edition, Edition.book_id == Book.id)
            .where(col == isbn)
            .limit(1)
        )
        return (await self._s.execute(stmt)).scalar_one_or_none()

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    async def create(
        self,
        *,
        title: str,
        status: str = "wanted",
        system_confidence: float = 0.0,
        external_ids: dict[str, str] | None = None,
        original_title: str | None = None,
        original_language: str | None = None,
        publication_year: int | None = None,
        description: str | None = None,
        series_id: uuid.UUID | None = None,
        series_position: float | None = None,
    ) -> Book:
        book = Book(
            title=title,
            status=status,
            system_confidence=system_confidence,
            external_ids=external_ids or {},
            original_title=original_title,
            original_language=original_language,
            publication_year=publication_year,
            description=description,
            series_id=series_id,
            series_position=series_position,
        )
        self._s.add(book)
        await self._s.flush()
        await self._s.refresh(book)
        return book

    async def link_author(
        self,
        book_id: uuid.UUID,
        author_id: uuid.UUID,
        role: str = "primary",
        position: int | None = None,
    ) -> None:
        await self._s.execute(
            book_authors_table.insert().values(
                book_id=book_id,
                author_id=author_id,
                role=role,
                position=position,
            )
        )

    async def update(
        self,
        book_id: uuid.UUID,
        updates: dict[str, Any],
    ) -> Book | None:
        await self._s.execute(
            update(Book)
            .where(Book.id == book_id)
            .values(**updates, updated_at=datetime.now(tz=UTC))
        )
        await self._s.flush()
        return await self.get(book_id)

    async def soft_delete(self, book_id: uuid.UUID) -> bool | None:
        """Archive a book. Returns True on success, False if already archived, None if not found."""
        result = await self._s.execute(
            update(Book)
            .where(Book.id == book_id, Book.status != "archived")
            .values(status="archived", updated_at=datetime.now(tz=UTC))
        )
        await self._s.flush()
        if result.rowcount > 0:
            return True
        exists = await self._s.get(Book, book_id)
        return False if exists is not None else None

    async def hard_delete(self, book_id: uuid.UUID) -> bool:
        result = await self._s.execute(
            delete(Book).where(Book.id == book_id)
        )
        await self._s.flush()
        return result.rowcount > 0

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _apply_filters(self, stmt: Any, *, status: str | None, author_id: uuid.UUID | None,
                       series_id: uuid.UUID | None, monitored: bool | None) -> Any:
        if status is not None:
            stmt = stmt.where(Book.status == status)
        elif monitored is not None:
            # monitored=true  → status IN (wanted, monitored)
            # monitored=false → status IN (unmonitored, archived)
            active = ["wanted", "monitored"]
            inactive = ["unmonitored", "archived"]
            stmt = stmt.where(Book.status.in_(active if monitored else inactive))

        if series_id is not None:
            stmt = stmt.where(Book.series_id == series_id)

        if author_id is not None:
            stmt = stmt.join(
                book_authors_table,
                Book.id == book_authors_table.c.book_id,
            ).where(book_authors_table.c.author_id == author_id)

        return stmt

    def _apply_sort(self, stmt: Any, *, sort_key: str, sort_dir: str,
                    author_id_filter: uuid.UUID | None) -> Any:
        if sort_key == "author_name":
            if author_id_filter is None:
                # No existing join — add both association and author tables
                stmt = stmt.outerjoin(
                    book_authors_table,
                    (Book.id == book_authors_table.c.book_id)
                    & (book_authors_table.c.role == "primary"),
                ).outerjoin(Author, Author.id == book_authors_table.c.author_id)
            else:
                # _apply_filters already joined book_authors_table (all roles).
                # Add Author join and deduplicate in case a book has the author
                # in multiple roles.
                stmt = stmt.outerjoin(
                    Author, Author.id == book_authors_table.c.author_id
                ).distinct()
            col = Author.sort_name
        else:
            col = _SORT_COLUMNS.get(sort_key, Book.title)

        stmt = stmt.order_by(col.desc() if sort_dir == "desc" else col.asc())
        # Secondary sort by id for stable pagination
        stmt = stmt.order_by(Book.id.asc())
        return stmt

    async def _load_primary_authors(
        self, book_ids: set[uuid.UUID]
    ) -> dict[uuid.UUID, Author]:
        if not book_ids:
            return {}
        stmt = (
            select(Author, book_authors_table.c.book_id)
            .join(book_authors_table, Author.id == book_authors_table.c.author_id)
            .where(
                book_authors_table.c.book_id.in_(book_ids),
                book_authors_table.c.role == "primary",
            )
        )
        rows = (await self._s.execute(stmt)).all()
        # If multiple primaries exist (shouldn't happen), keep first seen
        result: dict[uuid.UUID, Author] = {}
        for author, book_id in rows:
            result.setdefault(book_id, author)
        return result

    async def get_series(self, series_id: uuid.UUID) -> Series | None:
        return await self._s.get(Series, series_id)
