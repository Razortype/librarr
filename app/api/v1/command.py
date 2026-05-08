from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_metadata_service
from app.core.exceptions import BookNotFoundError
from app.schemas.command import CommandRequest, CommandResponse
from app.services.book_service import BookService
from app.services.metadata import MetadataService

router = APIRouter()
logger = structlog.get_logger(__name__)

# BookSearch moved to POST /api/v1/book/{book_id}/search
_STUB_COMMANDS = {"RescanLibrary"}


def _book_service(meta: Annotated[MetadataService, Depends(get_metadata_service)]) -> BookService:
    return BookService(meta)


@router.post("", response_model=CommandResponse, status_code=201)
async def run_command(
    request: CommandRequest,
    svc: Annotated[BookService, Depends(_book_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CommandResponse:
    now = datetime.now(tz=UTC)
    command_id = str(uuid.uuid4())

    if request.name in _STUB_COMMANDS:
        # Queued but not yet implemented — honest about async status
        logger.warning("command_stub", name=request.name, command_id=command_id)
        return CommandResponse(
            id=command_id,
            name=request.name,
            status="queued",
            queued_at=now,
            started_at=None,
            ended_at=None,
            body=request.body,
        )

    if request.name == "RefreshBook":
        book_id_raw = request.body.get("bookId")
        if not book_id_raw:
            raise HTTPException(status_code=422, detail="RefreshBook requires body.bookId")
        try:
            book_id = uuid.UUID(str(book_id_raw))
        except ValueError:
            raise HTTPException(status_code=422, detail="body.bookId must be a valid UUID")

        # Inline execution — returns 'completed' synchronously.
        # Will become async when Arq command queue lands (see ROADMAP).
        try:
            await svc.refresh_book(book_id, db)
        except BookNotFoundError as exc:
            raise HTTPException(
                status_code=422,
                detail={"error": "command_target_invalid", "message": str(exc)},
            ) from exc
        ended = datetime.now(tz=UTC)
        return CommandResponse(
            id=command_id,
            name=request.name,
            status="completed",
            queued_at=now,
            started_at=now,
            ended_at=ended,
            body=request.body,
        )

    known = "RefreshBook, RescanLibrary"
    raise HTTPException(
        status_code=422,
        detail=f"Unknown command: {request.name!r}. Known commands: {known}",
    )
