from __future__ import annotations

import contextlib
from collections.abc import AsyncGenerator
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.crypto import decrypt_config, encrypt_config
from app.integrations.exceptions import (
    QBittorrentAuthError,
    QBittorrentError,
    QBittorrentForbiddenError,
    QBittorrentTimeoutError,
)
from app.integrations.qbittorrent.client import QBittorrentClient
from app.repositories.integration_config import IntegrationConfigRepository
from app.schemas.qbittorrent import (
    QBittorrentConfigIn,
    QBittorrentConfigOut,
    QBittorrentTestResult,
)

_TYPE = "qbittorrent"


@contextlib.asynccontextmanager
async def _build_client(
    host: str,
    port: int,
    username: str,
    password: str,
    use_https: bool,
) -> AsyncGenerator[QBittorrentClient]:
    scheme = "https" if use_https else "http"
    base_url = f"{scheme}://{host}:{port}"
    async with httpx.AsyncClient(
        base_url=base_url,
        timeout=httpx.Timeout(
            settings.http_timeout_read,
            connect=settings.http_timeout_connect,
        ),
    ) as http:
        yield QBittorrentClient(http, username=username, password=password)


async def test_connection(
    host: str,
    port: int,
    username: str,
    password: str,
    use_https: bool,
) -> QBittorrentTestResult:
    try:
        async with _build_client(host, port, username, password, use_https) as client:
            health = await client.health()
        return QBittorrentTestResult(ok=True, version=health.version)
    except QBittorrentAuthError:
        return QBittorrentTestResult(ok=False, error="invalid credentials")
    except QBittorrentForbiddenError:
        return QBittorrentTestResult(
            ok=False,
            error="forbidden — check Server domains in qBittorrent Web UI settings",
        )
    except QBittorrentTimeoutError:
        return QBittorrentTestResult(ok=False, error="connection timeout")
    except QBittorrentError as exc:
        return QBittorrentTestResult(ok=False, error=str(exc))


def _row_to_out(row: object, cfg: dict[str, Any]) -> QBittorrentConfigOut:
    from app.models.integration_config import IntegrationConfig

    assert isinstance(row, IntegrationConfig)
    return QBittorrentConfigOut(
        id=row.id,
        name=row.name,
        host=cfg["host"],
        port=cfg["port"],
        username=cfg["username"],
        use_https=cfg.get("use_https", False),
        enabled=row.enabled,
        last_test_at=row.last_test_at,
        last_test_ok=row.last_test_ok,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def get_config(session: AsyncSession) -> QBittorrentConfigOut | None:
    repo = IntegrationConfigRepository(session)
    row = await repo.get_by_type(_TYPE)
    if row is None:
        return None
    return _row_to_out(row, decrypt_config(row.config))


async def upsert_config(
    session: AsyncSession, config_in: QBittorrentConfigIn
) -> QBittorrentConfigOut:
    repo = IntegrationConfigRepository(session)
    config_dict = {
        "host": config_in.host,
        "port": config_in.port,
        "username": config_in.username,
        "password": config_in.password,
        "use_https": config_in.use_https,
    }
    row = await repo.upsert(
        _TYPE,
        name=config_in.name,
        config_bytes=encrypt_config(config_dict),
        enabled=config_in.enabled,
    )
    return _row_to_out(row, config_dict)


async def delete_config(session: AsyncSession) -> bool:
    repo = IntegrationConfigRepository(session)
    return await repo.delete_by_type(_TYPE)
