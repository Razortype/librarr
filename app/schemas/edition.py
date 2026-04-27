from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, field_validator


class EditionDetail(BaseModel):
    id: str
    book_id: str
    isbn_10: str | None
    isbn_13: str | None
    asin: str | None
    format: str | None
    language: str | None
    publisher: str | None
    publication_date: date | None
    page_count: int | None
    audio_duration_seconds: int | None
    narrators: list[str] | None
    translators: list[str] | None
    cover_url: str | None
    external_ids: dict[str, str]
    system_confidence: float
    user_confidence: float | None
    effective_confidence: float
    created_at: datetime
    updated_at: datetime

    @field_validator("external_ids", mode="before")
    @classmethod
    def _coerce_ext_ids(cls, v: dict) -> dict[str, str]:
        return {k: str(val) for k, val in v.items()}
