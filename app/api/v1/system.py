from __future__ import annotations

import importlib.metadata

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

_VERSION = importlib.metadata.version("librarr")


class StatusResponse(BaseModel):
    status: str
    version: str


@router.get("/status", response_model=StatusResponse)
async def get_status() -> StatusResponse:
    return StatusResponse(status="ok", version=_VERSION)
