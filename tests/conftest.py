from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from pathlib import Path

import httpx
import pytest
from httpx import ASGITransport

from app.main import app


@pytest.fixture
async def client() -> AsyncGenerator[httpx.AsyncClient]:
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


def load_fixture(relative_path: str) -> dict:
    """Load a JSON fixture file relative to tests/fixtures/."""
    fixture_path = Path(__file__).parent / "fixtures" / relative_path
    return json.loads(fixture_path.read_text())
