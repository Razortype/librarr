from __future__ import annotations

import contextlib
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import httpx

from app.integrations.exceptions import (
    ProwlarrAuthError,
    ProwlarrServerError,
    ProwlarrTimeoutError,
)
from app.schemas.prowlarr import ProwlarrHealth

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VALID_PAYLOAD = {
    "name": "Local Prowlarr",
    "base_url": "http://localhost:9696",
    "api_key": "abc123",
    "enabled": True,
}

_TEST_PAYLOAD = {
    "base_url": "http://localhost:9696",
    "api_key": "abc123",
}


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
# GET /api/v1/integrations/prowlarr
# ---------------------------------------------------------------------------


async def test_get_returns_null_when_not_configured(api_client: httpx.AsyncClient) -> None:
    response = await api_client.get("/api/v1/integrations/prowlarr")
    assert response.status_code == 200
    assert response.json() is None


async def test_get_returns_config_after_put(api_client: httpx.AsyncClient) -> None:
    await api_client.put("/api/v1/integrations/prowlarr", json=_VALID_PAYLOAD)

    response = await api_client.get("/api/v1/integrations/prowlarr")
    assert response.status_code == 200
    data = response.json()
    assert data["base_url"] == "http://localhost:9696"
    assert "api_key" not in data


# ---------------------------------------------------------------------------
# PUT /api/v1/integrations/prowlarr
# ---------------------------------------------------------------------------


async def test_put_creates_config(api_client: httpx.AsyncClient) -> None:
    response = await api_client.put("/api/v1/integrations/prowlarr", json=_VALID_PAYLOAD)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Local Prowlarr"
    assert data["base_url"] == "http://localhost:9696"
    assert "api_key" not in data


async def test_put_replaces_existing_config(api_client: httpx.AsyncClient) -> None:
    await api_client.put("/api/v1/integrations/prowlarr", json=_VALID_PAYLOAD)

    updated = {**_VALID_PAYLOAD, "base_url": "http://192.168.1.10:9696", "name": "Updated"}
    response = await api_client.put("/api/v1/integrations/prowlarr", json=updated)
    assert response.status_code == 200
    data = response.json()
    assert data["base_url"] == "http://192.168.1.10:9696"
    assert data["name"] == "Updated"


async def test_put_returns_422_for_missing_required_field(api_client: httpx.AsyncClient) -> None:
    bad = {"name": "Prowlarr", "base_url": "http://localhost:9696"}  # api_key missing
    response = await api_client.put("/api/v1/integrations/prowlarr", json=bad)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# DELETE /api/v1/integrations/prowlarr
# ---------------------------------------------------------------------------


async def test_delete_returns_204(api_client: httpx.AsyncClient) -> None:
    await api_client.put("/api/v1/integrations/prowlarr", json=_VALID_PAYLOAD)
    response = await api_client.delete("/api/v1/integrations/prowlarr")
    assert response.status_code == 204


async def test_delete_returns_404_when_not_configured(api_client: httpx.AsyncClient) -> None:
    response = await api_client.delete("/api/v1/integrations/prowlarr")
    assert response.status_code == 404


async def test_delete_then_get_returns_null(api_client: httpx.AsyncClient) -> None:
    await api_client.put("/api/v1/integrations/prowlarr", json=_VALID_PAYLOAD)
    await api_client.delete("/api/v1/integrations/prowlarr")

    response = await api_client.get("/api/v1/integrations/prowlarr")
    assert response.status_code == 200
    assert response.json() is None


# ---------------------------------------------------------------------------
# POST /api/v1/integrations/prowlarr/test
# ---------------------------------------------------------------------------


async def test_test_endpoint_success(api_client: httpx.AsyncClient) -> None:
    mock_factory = make_mock_build_client(
        health_return=ProwlarrHealth(version="1.5.0", app_name="Prowlarr")
    )
    with patch("app.services.prowlarr_service._build_client", mock_factory):
        response = await api_client.post(
            "/api/v1/integrations/prowlarr/test", json=_TEST_PAYLOAD
        )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["version"] == "1.5.0"


async def test_test_endpoint_auth_failure(api_client: httpx.AsyncClient) -> None:
    mock_factory = make_mock_build_client(
        health_side_effect=ProwlarrAuthError("invalid api key")
    )
    with patch("app.services.prowlarr_service._build_client", mock_factory):
        response = await api_client.post(
            "/api/v1/integrations/prowlarr/test", json=_TEST_PAYLOAD
        )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert data["error"] == "invalid API key"


async def test_test_endpoint_timeout(api_client: httpx.AsyncClient) -> None:
    mock_factory = make_mock_build_client(
        health_side_effect=ProwlarrTimeoutError("timed out")
    )
    with patch("app.services.prowlarr_service._build_client", mock_factory):
        response = await api_client.post(
            "/api/v1/integrations/prowlarr/test", json=_TEST_PAYLOAD
        )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert data["error"] == "connection timeout"


async def test_test_endpoint_generic_error(api_client: httpx.AsyncClient) -> None:
    mock_factory = make_mock_build_client(
        health_side_effect=ProwlarrServerError(status_code=500, message="internal error")
    )
    with patch("app.services.prowlarr_service._build_client", mock_factory):
        response = await api_client.post(
            "/api/v1/integrations/prowlarr/test", json=_TEST_PAYLOAD
        )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert "500" in data["error"]
