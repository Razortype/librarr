from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.qbittorrent_service as qbt_service
from app.core.db import get_db
from app.schemas.qbittorrent import (
    QBittorrentConfigIn,
    QBittorrentConfigOut,
    QBittorrentTestRequest,
    QBittorrentTestResult,
)

router = APIRouter()

_DB = Annotated[AsyncSession, Depends(get_db)]


@router.get("/qbittorrent", response_model=QBittorrentConfigOut | None)
async def get_qbittorrent(session: _DB) -> QBittorrentConfigOut | None:
    return await qbt_service.get_config(session)


@router.put("/qbittorrent", response_model=QBittorrentConfigOut)
async def upsert_qbittorrent(
    body: QBittorrentConfigIn, session: _DB
) -> QBittorrentConfigOut:
    return await qbt_service.upsert_config(session, body)


@router.delete("/qbittorrent", status_code=204)
async def delete_qbittorrent(session: _DB) -> None:
    deleted = await qbt_service.delete_config(session)
    if not deleted:
        raise HTTPException(status_code=404, detail="qBittorrent not configured")


@router.post("/qbittorrent/test", response_model=QBittorrentTestResult)
async def test_qbittorrent(body: QBittorrentTestRequest) -> QBittorrentTestResult:
    return await qbt_service.test_connection(
        body.host, body.port, body.username, body.password, body.use_https
    )
