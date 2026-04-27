from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import httpx
import pytest
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.db import get_db
from app.core.deps import get_metadata_service
from app.main import app

# Import all models so Base.metadata is fully populated before create_all
from app.models.activity_log import ActivityLog  # noqa: F401
from app.models.associations import book_authors_table  # noqa: F401
from app.models.author import Author  # noqa: F401
from app.models.base import Base
from app.models.book import Book  # noqa: F401
from app.models.download import Download  # noqa: F401
from app.models.edition import Edition  # noqa: F401
from app.models.integration_config import IntegrationConfig  # noqa: F401
from app.models.metadata_cache import MetadataCache  # noqa: F401
from app.models.quality_profile import QualityProfile  # noqa: F401
from app.models.series import Series  # noqa: F401
from app.models.setting import Setting  # noqa: F401
from app.schemas.metadata import AuthorStub, BookMetadata, EditionMetadata

# ---------------------------------------------------------------------------
# Default metadata helpers
# ---------------------------------------------------------------------------


def _default_book_meta(title: str) -> BookMetadata:
    return BookMetadata(
        ol_work_id="OL12345W",
        title=title,
        original_language="en",
        publication_year=2020,
        description="A test description.",
        authors=[AuthorStub(ol_id="OL999A", name="Test Author")],
        cover_url=None,
        external_ids={"openlibrary_work": "OL12345W"},
        system_confidence=0.8,
    )


def _default_work_meta() -> BookMetadata:
    return BookMetadata(
        ol_work_id="OL12345W",
        title="Test Book",
        original_language="en",
        publication_year=2020,
        description="A test description.",
        authors=[AuthorStub(ol_id="OL999A", name="Test Author")],
        cover_url=None,
        external_ids={"openlibrary_work": "OL12345W"},
        system_confidence=0.8,
    )


def _default_edition_meta(isbn: str) -> EditionMetadata:
    return EditionMetadata(
        ol_edition_id="OL7000M",
        ol_work_id="OL12345W",
        isbn_13=isbn if len(isbn) == 13 else None,
        isbn_10=isbn if len(isbn) == 10 else None,
        title="Test Book",
        publisher="Test Publisher",
        publication_date=date(2020, 1, 1),
        page_count=300,
        language="en",
        format="paperback",
        cover_url=None,
        external_ids={
            "openlibrary_edition": "OL7000M",
            "openlibrary_work": "OL12345W",
        },
        system_confidence=0.8,
    )


# ---------------------------------------------------------------------------
# Mock metadata service
# ---------------------------------------------------------------------------


@dataclass
class MockMetadataService:
    """Configurable mock for MetadataService in endpoint tests.

    Defaults return plausible data (system_confidence=0.8, metadata_status=resolved).
    Set fail=True for total metadata unavailability.
    Set *_not_found=True or supply explicit *_result to override per-call behavior.
    """

    fail: bool = False

    # search_books — None means use _default_book_meta(title)
    search_results: list[BookMetadata] | None = None
    search_not_found: bool = False

    # lookup_by_isbn — None means use _default_edition_meta(isbn)
    isbn_result: EditionMetadata | None = None
    isbn_not_found: bool = False

    # lookup_work — None means use _default_work_meta()
    work_result: BookMetadata | None = None
    work_not_found: bool = False

    async def search_books(
        self, title: str, author: str | None = None
    ) -> list[BookMetadata]:
        if self.fail or self.search_not_found:
            return []
        if self.search_results is not None:
            return self.search_results
        return [_default_book_meta(title)]

    async def lookup_by_isbn(self, isbn: str) -> EditionMetadata | None:
        if self.fail or self.isbn_not_found:
            return None
        if self.isbn_result is not None:
            return self.isbn_result
        return _default_edition_meta(isbn)

    async def lookup_work(self, ol_work_id: str) -> BookMetadata | None:
        if self.fail or self.work_not_found:
            return None
        if self.work_result is not None:
            return self.work_result
        return _default_work_meta()

    async def lookup_author(self, ol_author_id: str) -> None:
        return None


# ---------------------------------------------------------------------------
# Shared DB fixture (in-memory SQLite, function scope)
# ---------------------------------------------------------------------------


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session: AsyncSession = async_session()
    try:
        yield session
    finally:
        await session.close()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()


# ---------------------------------------------------------------------------
# API client fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_metadata_service() -> MockMetadataService:
    return MockMetadataService()


@pytest.fixture
async def api_client(
    db_session: AsyncSession,
    mock_metadata_service: MockMetadataService,
) -> AsyncGenerator[httpx.AsyncClient]:
    """AsyncClient against the full app with in-memory DB + mock metadata service."""

    async def _override_get_db() -> AsyncGenerator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_metadata_service] = lambda: mock_metadata_service

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_metadata_service, None)


@pytest.fixture
async def api_client_with_real_metadata(
    db_session: AsyncSession,
) -> AsyncGenerator[httpx.AsyncClient]:
    """AsyncClient with in-memory DB + real MetadataService backed by 404 MockTransport.

    All OL/cloud HTTP calls return 404, so metadata is always unavailable.
    Tests that need specific responses should supply a custom MockTransport via
    dependency_overrides after receiving this fixture's client.
    """
    from app.integrations.librarr_cloud.client import CloudClient
    from app.integrations.openlibrary.client import OpenLibraryClient
    from app.services.metadata import MetadataService

    class _NotFoundTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, json={"error": "not found"})

    def _make_real_service() -> MetadataService:
        transport = _NotFoundTransport()
        ol_http = httpx.AsyncClient(
            base_url="https://openlibrary.org", transport=transport
        )
        cloud_http = httpx.AsyncClient(
            base_url="https://api.librarr.com", transport=transport
        )
        return MetadataService(
            ol_client=OpenLibraryClient(ol_http),
            cloud_client=CloudClient(cloud_http, api_key="test-key"),
        )

    async def _override_get_db() -> AsyncGenerator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_metadata_service] = _make_real_service

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_metadata_service, None)


# ---------------------------------------------------------------------------
# Existing fixtures (unchanged)
# ---------------------------------------------------------------------------


@pytest.fixture
async def client() -> AsyncGenerator[httpx.AsyncClient]:
    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


def load_fixture(relative_path: str) -> dict:
    """Load a JSON fixture file relative to tests/fixtures/."""
    fixture_path = Path(__file__).parent / "fixtures" / relative_path
    return json.loads(fixture_path.read_text())
