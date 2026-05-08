from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


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
