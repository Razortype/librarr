from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class OLSearchDoc(BaseModel):
    model_config = ConfigDict(extra="ignore")

    key: str  # "/works/OLxxxxxW"
    title: str
    author_name: list[str] | None = None
    author_key: list[str] | None = None  # parallel to author_name, may be shorter
    first_publish_year: int | None = None
    isbn: list[str] | None = None  # mixed ISBN-10 and ISBN-13
    cover_i: int | None = None
    language: list[str] | None = None  # OL 3-letter codes
    series: list[str] | None = None


class OLSearchResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    docs: list[OLSearchDoc] = Field(default_factory=list)
    num_found: int = 0


class OLWorkResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    key: str
    title: str
    description: str | dict | None = None  # polymorphic: str or {"type": ..., "value": "..."}


class OLAuthorResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    key: str
    name: str
    alternate_names: list[str] | None = None
    birth_date: str | None = None
    death_date: str | None = None
    bio: str | dict | None = None  # polymorphic: str or {"type": ..., "value": "..."}
    photos: list[int] | None = None


class OLEditionResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    key: str  # "/books/OLxxxxxM"
    title: str
    works: list[dict] | None = None  # [{"key": "/works/OLxxxxxW"}]
    isbn_10: list[str] | None = None
    isbn_13: list[str] | None = None
    publishers: list[str] | None = None
    publish_date: str | None = None
    number_of_pages: int | None = None
    languages: list[dict] | None = None  # [{"key": "/languages/eng"}]
    covers: list[int] | None = None
    physical_format: str | None = None
