from __future__ import annotations

import contextlib
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.exceptions import (
    QBittorrentAuthError,
    QBittorrentForbiddenError,
    QBittorrentTimeoutError,
)
from app.schemas.qbittorrent import QBittorrentConfigIn, QBittorrentHealth, QBittorrentTestResult
from app.services import qbittorrent_service as svc

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CONFIG_IN = QBittorrentConfigIn(
    name="Local qBit",
    host="localhost",
    port=8080,
    username="admin",
    password="s3cr3t",
    use_https=False,
    enabled=True,
)


def make_mock_build_client(
    health_return: QBittorrentHealth | None = None,
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

    assert result.name == "Local qBit"
    assert result.host == "localhost"
    assert result.port == 8080
    assert result.username == "admin"
    assert result.use_https is False
    assert result.enabled is True
    assert not hasattr(result, "password")


async def test_upsert_replaces_existing_config(db_session: AsyncSession) -> None:
    await svc.upsert_config(db_session, _CONFIG_IN)

    updated = QBittorrentConfigIn(
        name="Updated qBit",
        host="192.168.1.10",
        port=9090,
        username="newuser",
        password="newpass",
        use_https=True,
        enabled=False,
    )
    result = await svc.upsert_config(db_session, updated)

    assert result.name == "Updated qBit"
    assert result.host == "192.168.1.10"
    assert result.port == 9090
    assert result.username == "newuser"
    assert result.use_https is True
    assert result.enabled is False

    # Only one row in DB
    second_get = await svc.get_config(db_session)
    assert second_get is not None
    assert second_get.host == "192.168.1.10"


async def test_get_returns_decrypted_config_without_password(db_session: AsyncSession) -> None:
    await svc.upsert_config(db_session, _CONFIG_IN)

    result = await svc.get_config(db_session)

    assert result is not None
    assert result.host == "localhost"
    assert result.username == "admin"
    assert not hasattr(result, "password")


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
        health_return=QBittorrentHealth(version="v5.0.5")
    )
    with patch("app.services.qbittorrent_service._build_client", mock_factory):
        result = await svc.test_connection("localhost", 8080, "admin", "pass", False)

    assert result == QBittorrentTestResult(ok=True, version="v5.0.5")


async def test_test_connection_auth_failure() -> None:
    mock_factory = make_mock_build_client(health_side_effect=QBittorrentAuthError("bad creds"))
    with patch("app.services.qbittorrent_service._build_client", mock_factory):
        result = await svc.test_connection("localhost", 8080, "admin", "wrong", False)

    assert result == QBittorrentTestResult(ok=False, error="invalid credentials")


async def test_test_connection_timeout() -> None:
    mock_factory = make_mock_build_client(health_side_effect=QBittorrentTimeoutError("timeout"))
    with patch("app.services.qbittorrent_service._build_client", mock_factory):
        result = await svc.test_connection("localhost", 8080, "admin", "pass", False)

    assert result == QBittorrentTestResult(ok=False, error="connection timeout")


async def test_test_connection_forbidden() -> None:
    mock_factory = make_mock_build_client(
        health_side_effect=QBittorrentForbiddenError("forbidden")
    )
    with patch("app.services.qbittorrent_service._build_client", mock_factory):
        result = await svc.test_connection("localhost", 8080, "admin", "pass", False)

    assert result == QBittorrentTestResult(
        ok=False,
        error="forbidden — check Server domains in qBittorrent Web UI settings",
    )
