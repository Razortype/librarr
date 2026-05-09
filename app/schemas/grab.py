from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from app.schemas.release import ReleaseResult


class GrabStatus(StrEnum):
    GRABBED = "grabbed"


class GrabRequest(BaseModel):
    release_guid: str
    release_data: ReleaseResult


class GrabResponse(BaseModel):
    id: uuid.UUID
    book_id: uuid.UUID
    release_title: str
    indexer_name: str
    size_bytes: int
    qbit_hash: str
    status: GrabStatus
    grabbed_at: datetime

    model_config = ConfigDict(from_attributes=True)
