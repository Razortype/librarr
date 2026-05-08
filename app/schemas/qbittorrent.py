from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class QBittorrentHealth(BaseModel):
    """qBittorrent version. Used for test-connection."""

    version: str


class QBittorrentConfigIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    host: str = Field(min_length=1)
    port: int = Field(ge=1, le=65535)
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
    use_https: bool = False
    enabled: bool = True


class QBittorrentConfigOut(BaseModel):
    id: uuid.UUID
    name: str
    host: str
    port: int
    username: str
    use_https: bool
    enabled: bool
    last_test_at: datetime | None
    last_test_ok: bool | None
    created_at: datetime
    updated_at: datetime


class QBittorrentTestRequest(BaseModel):
    host: str
    port: int = Field(ge=1, le=65535)
    username: str
    password: str
    use_https: bool = False


class QBittorrentTestResult(BaseModel):
    ok: bool
    version: str | None = None
    error: str | None = None
