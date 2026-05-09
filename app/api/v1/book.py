from __future__ import annotations

import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_metadata_service, get_prowlarr_client
from app.integrations.exceptions import (
    ProwlarrAuthError,
    ProwlarrNotConfiguredError,
    ProwlarrRateLimitError,
    ProwlarrServerError,
    ProwlarrTimeoutError,
)
from app.integrations.prowlarr.client import ProwlarrClient
from app.schemas.book import (
    AddBookRequest,
    BookCreateResponse,
    BookDetail,
    BookListItem,
    BookPatchRequest,
    BookSearchQuery,
    BookSearchResponse,
    BookSearchResult,
)
from app.schemas.common import PaginatedResponse
from app.schemas.prowlarr import ProwlarrRelease
from app.schemas.release import ReleaseSearchResponse
from app.services import release_search_service
from app.services.book_service import BookService
from app.services.metadata import MetadataService

router = APIRouter()

_SORT_KEYS = {"title", "publication_year", "added_at", "effective_confidence", "author_name"}


def _book_service(meta: Annotated[MetadataService, Depends(get_metadata_service)]) -> BookService:
    return BookService(meta)


@router.post("", response_model=BookCreateResponse, status_code=201)
async def add_book(
    request: AddBookRequest,
    svc: Annotated[BookService, Depends(_book_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BookCreateResponse:
    return await svc.add_book(request, db)


@router.get("", response_model=PaginatedResponse[BookListItem])
async def list_books(
    svc: Annotated[BookService, Depends(_book_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status: Annotated[
        Literal["wanted", "monitored", "unmonitored", "archived"] | None, Query()
    ] = None,
    author_id: Annotated[uuid.UUID | None, Query()] = None,
    series_id: Annotated[uuid.UUID | None, Query()] = None,
    monitored: Annotated[bool | None, Query()] = None,
    sort_key: Annotated[str, Query()] = "title",
    sort_dir: Annotated[str, Query(pattern="^(asc|desc)$")] = "asc",
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PaginatedResponse[BookListItem]:
    if sort_key not in _SORT_KEYS:
        sort_key = "title"
    return await svc.list_books(
        db,
        status=status,
        author_id=author_id,
        series_id=series_id,
        monitored=monitored,
        sort_key=sort_key,
        sort_dir=sort_dir,
        limit=limit,
        offset=offset,
    )


@router.get("/search", response_model=BookSearchResponse)
async def search_books(
    title: Annotated[str, Query(min_length=1, max_length=200)],
    meta: Annotated[MetadataService, Depends(get_metadata_service)],
    author: Annotated[str | None, Query(max_length=200)] = None,
) -> BookSearchResponse:
    results = await meta.search_books(title=title, author=author)
    return BookSearchResponse(
        query=BookSearchQuery(title=title, author=author),
        results=[
            BookSearchResult(
                ol_work_id=r.ol_work_id,
                title=r.title,
                authors=r.authors,
                publication_year=r.publication_year,
                cover_url=r.cover_url,
                series_names=r.series_names,
                system_confidence=r.system_confidence,
            )
            for r in results
        ],
        total=len(results),
    )


@router.get("/{book_id}", response_model=BookDetail)
async def get_book(
    book_id: uuid.UUID,
    svc: Annotated[BookService, Depends(_book_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BookDetail:
    return await svc.get_book(book_id, db)


@router.patch("/{book_id}", response_model=BookDetail)
async def patch_book(
    book_id: uuid.UUID,
    patch: BookPatchRequest,
    svc: Annotated[BookService, Depends(_book_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BookDetail:
    return await svc.patch_book(book_id, patch, db)


@router.delete("/{book_id}")
async def delete_book(
    book_id: uuid.UUID,
    svc: Annotated[BookService, Depends(_book_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
    hard: Annotated[bool, Query()] = False,
) -> dict:
    return await svc.delete_book(book_id, db, hard=hard)


@router.post("/{book_id}/search", response_model=list[ProwlarrRelease])
async def search_book_releases_legacy(
    book_id: uuid.UUID,
    svc: Annotated[BookService, Depends(_book_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
    prowlarr: Annotated[ProwlarrClient, Depends(get_prowlarr_client)],
) -> list[ProwlarrRelease]:
    try:
        return await svc.search_releases(book_id, db, prowlarr)
    except ProwlarrAuthError:
        raise HTTPException(status_code=502, detail="Prowlarr authentication failed")
    except ProwlarrTimeoutError:
        raise HTTPException(status_code=503, detail="Prowlarr unreachable")
    except ProwlarrServerError as exc:
        raise HTTPException(status_code=502, detail=f"Prowlarr error: {str(exc)[:100]}")
    except ProwlarrRateLimitError as exc:
        raise HTTPException(
            status_code=429,
            detail="Prowlarr rate limited",
            headers={"Retry-After": str(exc.retry_after or 60)},
        )


@router.post("/{book_id}/release-search", response_model=ReleaseSearchResponse)
async def search_book_releases(
    book_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReleaseSearchResponse:
    try:
        return await release_search_service.search_releases(db, book_id)
    except ProwlarrNotConfiguredError:
        raise HTTPException(
            status_code=412,
            detail="Prowlarr is not configured. Configure it in integration settings.",
        )
    except ProwlarrAuthError:
        raise HTTPException(status_code=502, detail="Prowlarr authentication failed")
    except ProwlarrTimeoutError:
        raise HTTPException(status_code=504, detail="Prowlarr request timed out")
    except ProwlarrServerError as exc:
        raise HTTPException(status_code=502, detail=f"Prowlarr error: {str(exc)[:100]}")
    except ProwlarrRateLimitError as exc:
        raise HTTPException(
            status_code=429,
            detail="Prowlarr rate limited",
            headers={"Retry-After": str(exc.retry_after or 60)},
        )
