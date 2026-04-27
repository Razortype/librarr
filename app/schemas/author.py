from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, field_validator

from app.schemas.book import BookListItem
from app.schemas.common import PaginatedResponse


class AuthorDetail(BaseModel):
    id: str
    canonical_name: str
    sort_name: str
    aliases: list[str]
    birth_year: int | None
    death_year: int | None
    biography: str | None
    image_url: str | None
    external_ids: dict[str, str]
    system_confidence: float
    user_confidence: float | None
    effective_confidence: float
    created_at: datetime
    updated_at: datetime
    books: PaginatedResponse[BookListItem] | None = None

    @field_validator("external_ids", mode="before")
    @classmethod
    def _coerce_ext_ids(cls, v: dict) -> dict[str, str]:
        return {k: str(val) for k, val in v.items()}
