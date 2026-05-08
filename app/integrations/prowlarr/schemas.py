from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProwlarrSearchResultRaw(BaseModel):
    """Raw release object from GET /api/v1/search."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    guid: str
    title: str
    indexer_id: int = Field(alias="indexerId")
    indexer: str
    size: int
    publish_date: datetime = Field(alias="publishDate")
    download_url: str = Field(alias="downloadUrl")
    info_url: str | None = Field(default=None, alias="infoUrl")
    seeders: int | None = None
    leechers: int | None = None
    protocol: str  # "torrent" | "usenet"


class ProwlarrSystemStatusRaw(BaseModel):
    """Raw response from GET /api/v1/system/status."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    version: str
    app_name: str = Field(alias="appName")
