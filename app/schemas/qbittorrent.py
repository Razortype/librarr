from __future__ import annotations

from pydantic import BaseModel


class QBittorrentHealth(BaseModel):
    """qBittorrent version. Used for test-connection."""

    version: str
