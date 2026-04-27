from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_metadata_service
from app.schemas.author import AuthorDetail
from app.schemas.book import BookListItem
from app.schemas.common import PaginatedResponse
from app.services.book_service import BookService
from app.services.metadata import MetadataService

router = APIRouter()


def _book_service(meta: Annotated[MetadataService, Depends(get_metadata_service)]) -> BookService:
    return BookService(meta)


@router.get("/{author_id}", response_model=AuthorDetail)
async def get_author(
    author_id: uuid.UUID,
    svc: Annotated[BookService, Depends(_book_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthorDetail:
    return await svc.get_author(author_id, db)


@router.get("/{author_id}/book", response_model=PaginatedResponse[BookListItem])
async def list_author_books(
    author_id: uuid.UUID,
    svc: Annotated[BookService, Depends(_book_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PaginatedResponse[BookListItem]:
    return await svc.list_books(db, author_id=author_id, limit=limit, offset=offset)
