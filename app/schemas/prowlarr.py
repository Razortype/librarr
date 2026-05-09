from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ProwlarrRelease(BaseModel):
    """Normalized release returned by ProwlarrClient.search()."""

    guid: str
    title: str
    indexer_name: str
    size_bytes: int
    publish_date: datetime
    download_url: str
    info_url: str | None
    seeders: int | None
    leechers: int | None
    protocol: Literal["torrent", "usenet"]


class ProwlarrHealth(BaseModel):
    """Normalized response from ProwlarrClient.health()."""

    version: str
    app_name: str


class ProwlarrConfigIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    base_url: str = Field(min_length=1)
    api_key: str = Field(min_length=1)
    enabled: bool = True


class ProwlarrConfigOut(BaseModel):
    id: uuid.UUID
    name: str
    base_url: str
    enabled: bool
    last_test_at: datetime | None
    last_test_ok: bool | None
    created_at: datetime
    updated_at: datetime


class ProwlarrTestRequest(BaseModel):
    base_url: str
    api_key: str


class ProwlarrTestResult(BaseModel):
    ok: bool
    version: str | None = None
    error: str | None = None
