from __future__ import annotations

import importlib.metadata

import httpx


async def test_status_endpoint(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/system/status")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["version"] == importlib.metadata.version("librarr")
