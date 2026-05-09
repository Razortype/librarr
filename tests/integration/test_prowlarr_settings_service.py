from __future__ import annotations

import contextlib
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.exceptions import (
    ProwlarrAuthError,
    ProwlarrServerError,
    ProwlarrTimeoutError,
)
from app.schemas.prowlarr import ProwlarrConfigIn, ProwlarrHealth, ProwlarrTestResult
from app.services import prowlarr_service as svc

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CONFIG_IN = ProwlarrConfigIn(
    name="Local Prowlarr",
    base_url="http://localhost:9696",
    api_key="abc123",
    enabled=True,
)


def make_mock_build_client(
    health_return: ProwlarrHealth | None = None,
    health_side_effect: Exception | None = None,
) -> object:
    @contextlib.asynccontextmanager
    async def _ctx(*args: object, **kwargs: object) -> AsyncGenerator[AsyncMock]:
        mock_client = AsyncMock()
        if health_side_effect is not None:
            mock_client.health = AsyncMock(side_effect=health_side_effect)
        else:
            mock_client.health = AsyncMock(return_value=health_return)
        yield mock_client

    return _ctx


# ---------------------------------------------------------------------------
# CRUD — upsert / get / delete
# ---------------------------------------------------------------------------


async def test_upsert_creates_new_config(db_session: AsyncSession) -> None:
    result = await svc.upsert_config(db_session, _CONFIG_IN)

    assert result.name == "Local Prowlarr"
    assert result.base_url == "http://localhost:9696"
    assert result.enabled is True
    assert not hasattr(result, "api_key")


async def test_upsert_replaces_existing_config(db_session: AsyncSession) -> None:
    await svc.upsert_config(db_session, _CONFIG_IN)

    updated = ProwlarrConfigIn(
        name="Updated Prowlarr",
        base_url="http://192.168.1.10:9696",
        api_key="newkey",
        enabled=False,
    )
    result = await svc.upsert_config(db_session, updated)

    assert result.name == "Updated Prowlarr"
    assert result.base_url == "http://192.168.1.10:9696"
    assert result.enabled is False

    # Only one row in DB
    second_get = await svc.get_config(db_session)
    assert second_get is not None
    assert second_get.base_url == "http://192.168.1.10:9696"


async def test_get_returns_decrypted_config_without_api_key(db_session: AsyncSession) -> None:
    await svc.upsert_config(db_session, _CONFIG_IN)

    result = await svc.get_config(db_session)

    assert result is not None
    assert result.base_url == "http://localhost:9696"
    assert not hasattr(result, "api_key")


async def test_get_returns_none_when_not_configured(db_session: AsyncSession) -> None:
    result = await svc.get_config(db_session)
    assert result is None


async def test_delete_returns_true_when_exists(db_session: AsyncSession) -> None:
    await svc.upsert_config(db_session, _CONFIG_IN)
    assert await svc.delete_config(db_session) is True


async def test_delete_returns_false_when_not_configured(db_session: AsyncSession) -> None:
    assert await svc.delete_config(db_session) is False


# ---------------------------------------------------------------------------
# test_connection — mock _build_client
# ---------------------------------------------------------------------------


async def test_test_connection_success() -> None:
    mock_factory = make_mock_build_client(
        health_return=ProwlarrHealth(version="1.5.0", app_name="Prowlarr")
    )
    with patch("app.services.prowlarr_service._build_client", mock_factory):
        result = await svc.test_connection("http://localhost:9696", "abc123")

    assert result == ProwlarrTestResult(ok=True, version="1.5.0")


async def test_test_connection_auth_failure() -> None:
    mock_factory = make_mock_build_client(
        health_side_effect=ProwlarrAuthError("invalid api key")
    )
    with patch("app.services.prowlarr_service._build_client", mock_factory):
        result = await svc.test_connection("http://localhost:9696", "wrongkey")

    assert result == ProwlarrTestResult(ok=False, error="invalid API key")


async def test_test_connection_timeout() -> None:
    mock_factory = make_mock_build_client(
        health_side_effect=ProwlarrTimeoutError("timed out")
    )
    with patch("app.services.prowlarr_service._build_client", mock_factory):
        result = await svc.test_connection("http://localhost:9696", "abc123")

    assert result == ProwlarrTestResult(ok=False, error="connection timeout")


async def test_test_connection_generic_error() -> None:
    mock_factory = make_mock_build_client(
        health_side_effect=ProwlarrServerError(status_code=500, message="internal error")
    )
    with patch("app.services.prowlarr_service._build_client", mock_factory):
        result = await svc.test_connection("http://localhost:9696", "abc123")

    assert result.ok is False
    assert result.error is not None
    assert "500" in result.error
