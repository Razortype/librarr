from __future__ import annotations

import contextlib
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import httpx

from app.integrations.exceptions import (
    QBittorrentAuthError,
    QBittorrentForbiddenError,
    QBittorrentTimeoutError,
)
from app.schemas.qbittorrent import QBittorrentHealth

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VALID_PAYLOAD = {
    "name": "Local qBit",
    "host": "localhost",
    "port": 8080,
    "username": "admin",
    "password": "s3cr3t",
    "use_https": False,
    "enabled": True,
}


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
# GET /api/v1/integrations/qbittorrent
# ---------------------------------------------------------------------------


async def test_get_returns_null_when_not_configured(api_client: httpx.AsyncClient) -> None:
    response = await api_client.get("/api/v1/integrations/qbittorrent")
    assert response.status_code == 200
    assert response.json() is None


async def test_get_returns_config_after_put(api_client: httpx.AsyncClient) -> None:
    await api_client.put("/api/v1/integrations/qbittorrent", json=_VALID_PAYLOAD)

    response = await api_client.get("/api/v1/integrations/qbittorrent")
    assert response.status_code == 200
    data = response.json()
    assert data["host"] == "localhost"
    assert data["username"] == "admin"
    assert "password" not in data


# ---------------------------------------------------------------------------
# PUT /api/v1/integrations/qbittorrent
# ---------------------------------------------------------------------------


async def test_put_creates_config(api_client: httpx.AsyncClient) -> None:
    response = await api_client.put("/api/v1/integrations/qbittorrent", json=_VALID_PAYLOAD)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Local qBit"
    assert data["host"] == "localhost"
    assert data["port"] == 8080
    assert "password" not in data


async def test_put_replaces_existing_config(api_client: httpx.AsyncClient) -> None:
    await api_client.put("/api/v1/integrations/qbittorrent", json=_VALID_PAYLOAD)

    updated = {**_VALID_PAYLOAD, "host": "192.168.1.10", "port": 9090, "name": "Updated"}
    response = await api_client.put("/api/v1/integrations/qbittorrent", json=updated)
    assert response.status_code == 200
    data = response.json()
    assert data["host"] == "192.168.1.10"
    assert data["port"] == 9090
    assert data["name"] == "Updated"


async def test_put_returns_422_for_invalid_port(api_client: httpx.AsyncClient) -> None:
    bad = {**_VALID_PAYLOAD, "port": 99999}
    response = await api_client.put("/api/v1/integrations/qbittorrent", json=bad)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# DELETE /api/v1/integrations/qbittorrent
# ---------------------------------------------------------------------------


async def test_delete_returns_204(api_client: httpx.AsyncClient) -> None:
    await api_client.put("/api/v1/integrations/qbittorrent", json=_VALID_PAYLOAD)
    response = await api_client.delete("/api/v1/integrations/qbittorrent")
    assert response.status_code == 204


async def test_delete_returns_404_when_not_configured(api_client: httpx.AsyncClient) -> None:
    response = await api_client.delete("/api/v1/integrations/qbittorrent")
    assert response.status_code == 404


async def test_delete_then_get_returns_null(api_client: httpx.AsyncClient) -> None:
    await api_client.put("/api/v1/integrations/qbittorrent", json=_VALID_PAYLOAD)
    await api_client.delete("/api/v1/integrations/qbittorrent")

    response = await api_client.get("/api/v1/integrations/qbittorrent")
    assert response.status_code == 200
    assert response.json() is None


# ---------------------------------------------------------------------------
# POST /api/v1/integrations/qbittorrent/test
# ---------------------------------------------------------------------------

_TEST_PAYLOAD = {
    "host": "localhost",
    "port": 8080,
    "username": "admin",
    "password": "s3cr3t",
    "use_https": False,
}


async def test_test_endpoint_success(api_client: httpx.AsyncClient) -> None:
    mock_factory = make_mock_build_client(health_return=QBittorrentHealth(version="v5.0.5"))
    with patch("app.services.qbittorrent_service._build_client", mock_factory):
        response = await api_client.post(
            "/api/v1/integrations/qbittorrent/test", json=_TEST_PAYLOAD
        )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["version"] == "v5.0.5"


async def test_test_endpoint_auth_failure(api_client: httpx.AsyncClient) -> None:
    mock_factory = make_mock_build_client(
        health_side_effect=QBittorrentAuthError("bad creds")
    )
    with patch("app.services.qbittorrent_service._build_client", mock_factory):
        response = await api_client.post(
            "/api/v1/integrations/qbittorrent/test", json=_TEST_PAYLOAD
        )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert data["error"] == "invalid credentials"


async def test_test_endpoint_timeout(api_client: httpx.AsyncClient) -> None:
    mock_factory = make_mock_build_client(
        health_side_effect=QBittorrentTimeoutError("timeout")
    )
    with patch("app.services.qbittorrent_service._build_client", mock_factory):
        response = await api_client.post(
            "/api/v1/integrations/qbittorrent/test", json=_TEST_PAYLOAD
        )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert data["error"] == "connection timeout"


async def test_test_endpoint_forbidden(api_client: httpx.AsyncClient) -> None:
    mock_factory = make_mock_build_client(
        health_side_effect=QBittorrentForbiddenError("forbidden")
    )
    with patch("app.services.qbittorrent_service._build_client", mock_factory):
        response = await api_client.post(
            "/api/v1/integrations/qbittorrent/test", json=_TEST_PAYLOAD
        )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert "Server domains" in data["error"]
