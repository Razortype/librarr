from __future__ import annotations

import httpx
import pytest
from httpx import ASGITransport

from app.main import app


@pytest.fixture
async def client() -> httpx.AsyncClient:
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
