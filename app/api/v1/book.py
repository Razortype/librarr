from __future__ import annotations

import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_metadata_service
from app.schemas.book import (
    AddBookRequest,
    BookCreateResponse,
    BookDetail,
    BookListItem,
    BookPatchRequest,
)
from app.schemas.common import PaginatedResponse
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
