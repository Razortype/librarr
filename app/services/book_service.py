from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorNotFoundError, BookNotFoundError, DuplicateBookError
from app.repositories.author import AuthorRepository
from app.repositories.book import AuthorWithRole, BookRepository
from app.repositories.edition import EditionRepository
from app.schemas.author import AuthorDetail
from app.schemas.book import (
    BOOK_METADATA_FIELDS,
    AddBookRequest,
    AuthorInBook,
    AuthorRef,
    BookCreateResponse,
    BookDetail,
    BookListItem,
    BookPatchRequest,
    EditionInBook,
    IsbnLookup,
    SeriesRef,
    TitleAuthorLookup,
)
from app.schemas.common import PaginatedResponse

if TYPE_CHECKING:
    from app.models.author import Author
    from app.models.book import Book
    from app.models.edition import Edition
    from app.repositories.book import BookListRow
    from app.services.metadata import MetadataService

logger = structlog.get_logger(__name__)

# External ID sources checked in priority order for author dedup
_AUTHOR_DEDUP_SOURCES = ("openlibrary", "openlibrary_author", "goodreads", "isni", "wikidata")


class BookService:
    def __init__(self, metadata_svc: MetadataService) -> None:
        self._meta = metadata_svc

    # ------------------------------------------------------------------
    # Add book
    # ------------------------------------------------------------------

    async def add_book(self, request: AddBookRequest, db: AsyncSession) -> BookCreateResponse:
        books = BookRepository(db)
        editions = EditionRepository(db)

        if isinstance(request, IsbnLookup):
            existing = await books.get_by_isbn(request.isbn)
            if existing is not None:
                raise DuplicateBookError(isbn=request.isbn, existing_id=str(existing.id))

        warnings: list[str] = []
        metadata_status = "unresolved"
        book_title = request.title if isinstance(request, TitleAuthorLookup) else ""
        book_data: dict = {}
        edition_data: dict | None = None
        author_stubs: list = []
        system_confidence = 0.0

        if isinstance(request, IsbnLookup):
            result = await self._meta.lookup_by_isbn(request.isbn)
            if result is not None:
                book_title = result.title
                edition_data = {
                    "isbn_13": result.isbn_13,
                    "isbn_10": result.isbn_10,
                    "publisher": result.publisher,
                    "publication_date": result.publication_date,
                    "page_count": result.page_count,
                    "language": result.language,
                    "format": result.format,
                    "cover_url": result.cover_url,
                    "external_ids": result.external_ids,
                    "system_confidence": result.system_confidence,
                }
                system_confidence = result.system_confidence
                metadata_status = "resolved" if result.system_confidence >= 0.7 else "partial"

                # Try to enrich the work details from ol_work_id
                if result.ol_work_id:
                    try:
                        work = await self._meta.lookup_work(result.ol_work_id)
                    except Exception:  # noqa: BLE001 — intentional broad catch: any OL/cloud
                        # failure (timeout, parse error, 5xx) triggers graceful degradation
                        # rather than failing the entire add-book request.
                        work = None
                        warnings.append("Work details unavailable; edition metadata only.")
                    if work is not None:
                        book_data["description"] = work.description
                        book_data["publication_year"] = work.publication_year
                        book_data["external_ids"] = {
                            **result.external_ids,
                            **work.external_ids,
                        }
                        author_stubs = work.authors
            else:
                warnings.append(
                    f"No metadata found for ISBN {request.isbn}. "
                    "Book added with minimal data."
                )
                book_title = request.isbn
                edition_data = {
                    "isbn_13": request.isbn if len(request.isbn) == 13 else None,
                    "isbn_10": request.isbn if len(request.isbn) == 10 else None,
                    "system_confidence": 0.0,
                }

        else:  # TitleAuthorLookup
            results = await self._meta.search_books(
                title=request.title, author=request.author
            )
            if results:
                best = results[0]
                book_title = best.title
                book_data = {
                    "original_language": best.original_language,
                    "publication_year": best.publication_year,
                    "description": best.description,
                    "external_ids": best.external_ids,
                }
                author_stubs = best.authors
                system_confidence = best.system_confidence
                metadata_status = "resolved" if best.system_confidence >= 0.7 else "partial"
            else:
                warnings.append(
                    "No metadata found for this title/author. "
                    "Book added with minimal data."
                )

        # Persist within a single transaction
        book = await books.create(
            title=book_title,
            status="wanted",
            system_confidence=system_confidence,
            original_language=book_data.get("original_language"),
            publication_year=book_data.get("publication_year"),
            description=book_data.get("description"),
            external_ids=book_data.get("external_ids", {}),
        )

        if edition_data is not None:
            await editions.create(book_id=book.id, **edition_data)

        authors_repo = AuthorRepository(db)
        position = 0
        for stub in author_stubs:
            author = await self._dedup_or_create_author(
                authors_repo,
                name=stub.name,
                ol_id=stub.ol_id,
                system_confidence=system_confidence,
            )
            role = "primary" if position == 0 else "co_author"
            await books.link_author(book.id, author.id, role=role, position=position)
            position += 1

        await db.commit()
        # Reload via repository to get fresh scalars with populate_existing
        book = await books.get(book.id)  # type: ignore[assignment]

        book_detail = await self._build_book_detail(book, books, db)
        return BookCreateResponse(
            book=book_detail,
            metadata_status=metadata_status,
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # List books
    # ------------------------------------------------------------------

    async def list_books(
        self,
        db: AsyncSession,
        *,
        status: str | None = None,
        author_id: uuid.UUID | None = None,
        series_id: uuid.UUID | None = None,
        monitored: bool | None = None,
        sort_key: str = "title",
        sort_dir: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ) -> PaginatedResponse[BookListItem]:
        books = BookRepository(db)
        rows, total = await books.list(
            status=status,
            author_id=author_id,
            series_id=series_id,
            monitored=monitored,
            sort_key=sort_key,
            sort_dir=sort_dir,
            limit=limit,
            offset=offset,
        )
        items = [_row_to_list_item(row) for row in rows]
        return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)

    # ------------------------------------------------------------------
    # Get book
    # ------------------------------------------------------------------

    async def get_book(self, book_id: uuid.UUID, db: AsyncSession) -> BookDetail:
        books = BookRepository(db)
        book = await books.get(book_id)
        if book is None:
            raise BookNotFoundError(str(book_id))
        return await self._build_book_detail(book, books, db)

    # ------------------------------------------------------------------
    # Patch book
    # ------------------------------------------------------------------

    async def patch_book(
        self, book_id: uuid.UUID, patch: BookPatchRequest, db: AsyncSession
    ) -> BookDetail:
        books = BookRepository(db)
        existing = await books.get(book_id)
        if existing is None:
            raise BookNotFoundError(str(book_id))

        touched = patch.model_fields_set
        if not touched:
            return await self._build_book_detail(existing, books, db)

        updates: dict = {f: getattr(patch, f) for f in touched}

        if touched & BOOK_METADATA_FIELDS:
            updates["user_confidence"] = 1.0

        book = await books.update(book_id, updates)
        await db.commit()
        return await self._build_book_detail(book, books, db)

    # ------------------------------------------------------------------
    # Delete book
    # ------------------------------------------------------------------

    async def delete_book(
        self, book_id: uuid.UUID, db: AsyncSession, *, hard: bool = False
    ) -> dict:
        books = BookRepository(db)
        if hard:
            deleted = await books.hard_delete(book_id)
            if not deleted:
                raise BookNotFoundError(str(book_id))
            await db.commit()
            return {"deleted": True, "id": str(book_id)}

        archived = await books.soft_delete(book_id)
        if not archived:
            raise BookNotFoundError(str(book_id))
        await db.commit()
        return {"archived": True, "deleted": False, "id": str(book_id)}

    # ------------------------------------------------------------------
    # Refresh book (used by command handler)
    # ------------------------------------------------------------------

    async def refresh_book(self, book_id: uuid.UUID, db: AsyncSession) -> BookDetail:
        """Re-fetch metadata from cloud/OL for an existing book."""
        books = BookRepository(db)
        book = await books.get(book_id)
        if book is None:
            raise BookNotFoundError(str(book_id))

        # Build a title+author query from current data
        author_rows = await books.get_authors_for_book(book_id)
        primary_name: str | None = None
        if author_rows:
            primary_name = author_rows[0].author.canonical_name

        results = await self._meta.search_books(title=book.title, author=primary_name)
        if not results:
            return await self._build_book_detail(book, books, db)

        best = results[0]
        updates: dict = {}
        if best.publication_year and not book.publication_year:
            updates["publication_year"] = best.publication_year
        if best.description and not book.description:
            updates["description"] = best.description
        if best.system_confidence > book.system_confidence:
            updates["system_confidence"] = best.system_confidence
        if best.external_ids:
            updates["external_ids"] = {**book.external_ids, **best.external_ids}

        if updates:
            book = await books.update(book_id, updates)
            await db.commit()

        return await self._build_book_detail(book, books, db)

    # ------------------------------------------------------------------
    # Author detail
    # ------------------------------------------------------------------

    async def get_author(
        self,
        author_id: uuid.UUID,
        db: AsyncSession,
        *,
        include_books: bool = False,
        books_limit: int = 50,
        books_offset: int = 0,
    ) -> AuthorDetail:
        authors = AuthorRepository(db)
        author = await authors.get(author_id)
        if author is None:
            raise AuthorNotFoundError(str(author_id))

        books_page: PaginatedResponse[BookListItem] | None = None
        if include_books:
            books_page = await self.list_books(
                db, author_id=author_id, limit=books_limit, offset=books_offset
            )

        return _author_to_detail(author, books_page)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    async def _build_book_detail(
        self, book: Book, books: BookRepository, db: AsyncSession
    ) -> BookDetail:
        author_rows = await books.get_authors_for_book(book.id)

        # Explicitly query editions and cover — never access ORM relationships
        # to avoid synchronous lazy-load in async context.
        editions = await EditionRepository(db).list_by_book(book.id)
        cover_url = next((e.cover_url for e in editions if e.cover_url), None)
        if cover_url is None:
            cover_url = await books.get_cover_url(book.id)

        series: SeriesRef | None = None
        if book.series_id is not None:
            s = await books.get_series(book.series_id)
            if s:
                series = SeriesRef(
                    id=str(s.id),
                    name=s.name,
                    effective_confidence=s.effective_confidence,
                )

        return BookDetail(
            id=str(book.id),
            title=book.title,
            original_title=book.original_title,
            original_language=book.original_language,
            publication_year=book.publication_year,
            description=book.description,
            status=book.status,
            series=series,
            series_position=book.series_position,
            cover_url=cover_url,
            authors=[_author_with_role_to_schema(r) for r in author_rows],
            editions=[_edition_to_schema(e) for e in editions],
            external_ids={k: str(v) for k, v in (book.external_ids or {}).items()},
            system_confidence=book.system_confidence,
            user_confidence=book.user_confidence,
            effective_confidence=book.effective_confidence,
            created_at=book.created_at,
            updated_at=book.updated_at,
        )

    async def _dedup_or_create_author(
        self,
        repo: AuthorRepository,
        *,
        name: str,
        ol_id: str | None,
        system_confidence: float,
    ) -> Author:
        # Currently only OL provides external_ids; goodreads/isni/wikidata
        # become reachable when those metadata sources land (see FOLLOWUPS.md).
        # Priority 1–2: check known external ID sources
        if ol_id:
            for source in ("openlibrary_author", "openlibrary"):
                match = await repo.get_by_external_id(source, ol_id)
                if match:
                    await repo.merge_external_ids(match, {source: ol_id})
                    return match

        # Priority 3–4: name-based fallback
        match = await repo.get_by_name(name)
        if match:
            if ol_id:
                await repo.merge_external_ids(match, {"openlibrary_author": ol_id})
            return match

        # No match — create new
        sort_name = _derive_sort_name(name)
        ext_ids: dict[str, str] = {}
        if ol_id:
            ext_ids["openlibrary_author"] = ol_id

        return await repo.create(
            canonical_name=name,
            sort_name=sort_name,
            external_ids=ext_ids,
            system_confidence=system_confidence,
        )


# ------------------------------------------------------------------
# Pure conversion helpers (no async)
# ------------------------------------------------------------------


def _derive_sort_name(name: str) -> str:
    """'Ursula K. Le Guin' -> 'Le Guin, Ursula K.'  (best-effort last-name-first)."""
    parts = name.strip().split()
    if len(parts) <= 1:
        return name
    return f"{parts[-1]}, {' '.join(parts[:-1])}"


def _row_to_list_item(row: BookListRow) -> BookListItem:
    book = row.book
    primary: AuthorRef | None = None
    if row.primary_author:
        a = row.primary_author
        primary = AuthorRef(
            id=str(a.id),
            canonical_name=a.canonical_name,
            sort_name=a.sort_name,
            image_url=a.image_url,
            effective_confidence=a.effective_confidence,
        )
    return BookListItem(
        id=str(book.id),
        title=book.title,
        original_title=book.original_title,
        original_language=book.original_language,
        publication_year=book.publication_year,
        status=book.status,
        series_id=str(book.series_id) if book.series_id else None,
        series_position=book.series_position,
        cover_url=row.cover_url,
        primary_author=primary,
        external_ids={k: str(v) for k, v in (book.external_ids or {}).items()},
        effective_confidence=book.effective_confidence,
        updated_at=book.updated_at,
    )


def _author_with_role_to_schema(row: AuthorWithRole) -> AuthorInBook:
    a = row.author
    return AuthorInBook(
        id=str(a.id),
        canonical_name=a.canonical_name,
        sort_name=a.sort_name,
        role=row.role,
        position=row.position,
        effective_confidence=a.effective_confidence,
    )


def _edition_to_schema(e: Edition) -> EditionInBook:
    pub_date = e.publication_date if e.publication_date else None
    return EditionInBook(
        id=str(e.id),
        isbn_10=e.isbn_10,
        isbn_13=e.isbn_13,
        asin=e.asin,
        format=e.format,
        language=e.language,
        publisher=e.publisher,
        publication_date=pub_date,
        page_count=e.page_count,
        cover_url=e.cover_url,
        system_confidence=e.system_confidence,
        user_confidence=e.user_confidence,
        effective_confidence=e.effective_confidence,
    )


def _author_to_detail(
    author: Author,
    books: PaginatedResponse[BookListItem] | None,
) -> AuthorDetail:
    return AuthorDetail(
        id=str(author.id),
        canonical_name=author.canonical_name,
        sort_name=author.sort_name,
        aliases=author.aliases or [],
        birth_year=author.birth_year,
        death_year=author.death_year,
        biography=author.biography,
        image_url=author.image_url,
        external_ids={k: str(v) for k, v in (author.external_ids or {}).items()},
        system_confidence=author.system_confidence,
        user_confidence=author.user_confidence,
        effective_confidence=author.effective_confidence,
        created_at=author.created_at,
        updated_at=author.updated_at,
        books=books,
    )
