from __future__ import annotations

import re
import uuid
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator

# Fields on Book that represent metadata (not operational state).
# Touching any of these in a PATCH triggers user_confidence = 1.0.
BOOK_METADATA_FIELDS: frozenset[str] = frozenset(
    {
        "title",
        "original_title",
        "original_language",
        "publication_year",
        "description",
        "series_id",
        "series_position",
        "external_ids",
    }
)


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class TitleAuthorLookup(BaseModel):
    lookup_type: Literal["title_author"] = "title_author"
    title: str = Field(..., min_length=1)
    author: str | None = None


class IsbnLookup(BaseModel):
    lookup_type: Literal["isbn"] = "isbn"
    isbn: str

    @field_validator("isbn")
    @classmethod
    def validate_isbn(cls, v: str) -> str:
        digits = re.sub(r"[\s\-]", "", v)
        if len(digits) not in (10, 13) or not digits[:-1].isdigit():
            raise ValueError("ISBN must be 10 or 13 digits")
        return digits


AddBookRequest = Annotated[
    TitleAuthorLookup | IsbnLookup,
    Field(discriminator="lookup_type"),
]


class BookPatchRequest(BaseModel):
    status: Literal["wanted", "monitored", "unmonitored", "archived"] | None = None
    title: str | None = None
    original_title: str | None = None
    original_language: str | None = None
    publication_year: int | None = None
    description: str | None = None
    series_id: uuid.UUID | None = None
    series_position: float | None = None
    external_ids: dict[str, str] | None = None

    @field_validator("external_ids", mode="before")
    @classmethod
    def _coerce_ext_ids(cls, v: dict | None) -> dict[str, str] | None:
        if v is None:
            return None
        return {k: str(val) for k, val in v.items()}


# ---------------------------------------------------------------------------
# Embedded / nested response models
# ---------------------------------------------------------------------------


class SeriesRef(BaseModel):
    id: str
    name: str
    effective_confidence: float


class AuthorRef(BaseModel):
    """Denormalized primary-author snippet used in list items."""

    id: str
    canonical_name: str
    sort_name: str
    image_url: str | None
    effective_confidence: float


class AuthorInBook(BaseModel):
    """Full author row with M2M role/position, used in book detail."""

    id: str
    canonical_name: str
    sort_name: str
    role: Literal["primary", "co_author", "contributor", "translator", "illustrator"]
    position: int | None
    effective_confidence: float


class EditionInBook(BaseModel):
    id: str
    isbn_10: str | None
    isbn_13: str | None
    asin: str | None
    format: Literal[
        "hardcover", "paperback", "ebook", "audiobook", "large_print", "mass_market"
    ] | None
    language: str | None
    publisher: str | None
    publication_date: date | None
    page_count: int | None
    cover_url: str | None
    system_confidence: float
    user_confidence: float | None
    effective_confidence: float


# ---------------------------------------------------------------------------
# Top-level response models
# ---------------------------------------------------------------------------


class BookListItem(BaseModel):
    id: str
    title: str
    original_title: str | None
    original_language: str | None
    publication_year: int | None
    status: Literal["wanted", "monitored", "unmonitored", "archived"]
    series_id: str | None
    series_position: float | None
    cover_url: str | None
    primary_author: AuthorRef | None
    external_ids: dict[str, str]
    effective_confidence: float
    updated_at: datetime


class BookDetail(BaseModel):
    id: str
    title: str
    original_title: str | None
    original_language: str | None
    publication_year: int | None
    description: str | None
    status: Literal["wanted", "monitored", "unmonitored", "archived"]
    series: SeriesRef | None
    series_position: float | None
    cover_url: str | None
    authors: list[AuthorInBook]
    editions: list[EditionInBook]
    external_ids: dict[str, str]
    system_confidence: float
    user_confidence: float | None
    effective_confidence: float
    created_at: datetime
    updated_at: datetime


class BookCreateResponse(BaseModel):
    book: BookDetail
    metadata_status: Literal["resolved", "partial", "unresolved"]
    warnings: list[str]
