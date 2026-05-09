from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ReleaseResult(BaseModel):
    guid: str
    title: str
    indexer: str
    size_bytes: int
    seeders: int
    leechers: int
    publish_date: datetime | None
    download_url: str | None
    protocol: Literal["torrent"]
    detected_format: Literal["epub", "pdf", "mobi", "azw3", "unknown"]
    score: int


class ReleaseSearchResponse(BaseModel):
    query: str
    results: list[ReleaseResult]
    total: int
