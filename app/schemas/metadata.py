from __future__ import annotations

from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class AuthorStub(BaseModel):
    ol_id: str | None = None  # bare OL ID e.g. "OL26320A" (no path prefix)
    name: str


class AuthorMetadata(BaseModel):
    type: Literal["author"] = "author"
    ol_id: str  # bare OL ID e.g. "OL26320A"
    name: str
    alternate_names: list[str] | None = None
    birth_year: int | None = None
    death_year: int | None = None
    biography: str | None = None
    image_url: str | None = None
    external_ids: dict[str, str] = Field(default_factory=dict)
    system_confidence: float = 0.6


class BookMetadata(BaseModel):
    type: Literal["book"] = "book"
    ol_work_id: str | None = None  # bare OL work ID e.g. "OL45804W"
    title: str
    original_language: str | None = None  # ISO 639-1
    publication_year: int | None = None
    description: str | None = None  # absent from search results, populated from work endpoint
    authors: list[AuthorStub] = Field(default_factory=list)
    series_names: list[str] | None = None  # raw OL series strings, no position
    cover_url: str | None = None  # resolved from cover_i at normalization boundary
    external_ids: dict[str, str] = Field(default_factory=dict)
    system_confidence: float = 0.6


class EditionMetadata(BaseModel):
    type: Literal["edition"] = "edition"
    ol_edition_id: str | None = None  # bare OL edition ID e.g. "OL7353617M"
    ol_work_id: str | None = None  # extracted from works[0].key
    isbn_10: str | None = None
    isbn_13: str | None = None
    title: str
    publisher: str | None = None
    publication_date: date | None = None
    page_count: int | None = None
    language: str | None = None  # ISO 639-1
    format: str | None = None  # maps to EditionFormat enum values where possible
    cover_url: str | None = None
    external_ids: dict[str, str] = Field(default_factory=dict)
    system_confidence: float = 0.6


MetadataResult = Annotated[
    BookMetadata | AuthorMetadata | EditionMetadata,
    Field(discriminator="type"),
]
