from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class CommandRequest(BaseModel):
    name: str
    body: dict = {}


class CommandResponse(BaseModel):
    id: str
    name: str
    status: Literal["queued", "started", "completed", "failed"]
    queued_at: datetime
    started_at: datetime | None
    ended_at: datetime | None
    body: dict
