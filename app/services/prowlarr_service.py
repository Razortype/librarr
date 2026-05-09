from __future__ import annotations

import contextlib
from collections.abc import AsyncGenerator
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.crypto import decrypt_config, encrypt_config
from app.integrations.exceptions import (
    ProwlarrAuthError,
    ProwlarrError,
    ProwlarrTimeoutError,
)
from app.integrations.prowlarr.client import ProwlarrClient
from app.repositories.integration_config import IntegrationConfigRepository
from app.schemas.prowlarr import (
    ProwlarrConfigIn,
    ProwlarrConfigOut,
    ProwlarrTestResult,
)

_TYPE = "prowlarr"


@contextlib.asynccontextmanager
async def _build_client(base_url: str, api_key: str) -> AsyncGenerator[ProwlarrClient]:
    async with httpx.AsyncClient(
        base_url=base_url,
        timeout=httpx.Timeout(
            settings.http_timeout_read,
            connect=settings.http_timeout_connect,
        ),
    ) as http:
        yield ProwlarrClient(http, api_key=api_key)


async def test_connection(base_url: str, api_key: str) -> ProwlarrTestResult:
    try:
        async with _build_client(base_url, api_key) as client:
            health = await client.health()
        return ProwlarrTestResult(ok=True, version=health.version)
    except ProwlarrAuthError:
        return ProwlarrTestResult(ok=False, error="invalid API key")
    except ProwlarrTimeoutError:
        return ProwlarrTestResult(ok=False, error="connection timeout")
    except ProwlarrError as exc:
        return ProwlarrTestResult(ok=False, error=str(exc))


def _row_to_out(row: object, cfg: dict[str, Any]) -> ProwlarrConfigOut:
    from app.models.integration_config import IntegrationConfig

    assert isinstance(row, IntegrationConfig)
    return ProwlarrConfigOut(
        id=row.id,
        name=row.name,
        base_url=cfg["base_url"],
        enabled=row.enabled,
        last_test_at=row.last_test_at,
        last_test_ok=row.last_test_ok,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def get_config(session: AsyncSession) -> ProwlarrConfigOut | None:
    repo = IntegrationConfigRepository(session)
    row = await repo.get_by_type(_TYPE)
    if row is None:
        return None
    return _row_to_out(row, decrypt_config(row.config))


async def upsert_config(
    session: AsyncSession, config_in: ProwlarrConfigIn
) -> ProwlarrConfigOut:
    repo = IntegrationConfigRepository(session)
    config_dict = {
        "base_url": config_in.base_url,
        "api_key": config_in.api_key,
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
