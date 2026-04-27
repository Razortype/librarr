from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.exceptions import AuthorNotFoundError, BookNotFoundError, DuplicateBookError


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: dict = {}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(BookNotFoundError)
    async def _book_not_found(request: Request, exc: BookNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="not_found",
                message=str(exc),
                details={"book_id": exc.book_id},
            ).model_dump(),
        )

    @app.exception_handler(AuthorNotFoundError)
    async def _author_not_found(request: Request, exc: AuthorNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="not_found",
                message=str(exc),
                details={"author_id": exc.author_id},
            ).model_dump(),
        )

    @app.exception_handler(DuplicateBookError)
    async def _duplicate_book(request: Request, exc: DuplicateBookError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content=ErrorResponse(
                error="conflict",
                message=str(exc),
                details={"isbn": exc.isbn, "existing_book_id": exc.existing_id},
            ).model_dump(),
        )
