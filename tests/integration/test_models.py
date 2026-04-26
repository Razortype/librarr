from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Import all models so Base.metadata is fully populated before create_all
from app.models.activity_log import ActivityLog  # noqa: F401
from app.models.associations import book_authors_table  # noqa: F401
from app.models.author import Author
from app.models.base import Base
from app.models.book import Book
from app.models.download import Download  # noqa: F401
from app.models.edition import Edition
from app.models.integration_config import IntegrationConfig  # noqa: F401
from app.models.metadata_cache import MetadataCache  # noqa: F401
from app.models.quality_profile import QualityProfile  # noqa: F401
from app.models.series import Series
from app.models.setting import Setting  # noqa: F401


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore[call-overload]

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


async def test_create_and_read_author(db_session: AsyncSession) -> None:
    author = Author(
        canonical_name="Ursula K. Le Guin",
        sort_name="Le Guin, Ursula K.",
        system_confidence=0.9,
    )
    db_session.add(author)
    await db_session.flush()

    await db_session.refresh(author)

    assert author.canonical_name == "Ursula K. Le Guin"
    assert author.effective_confidence == 0.9


async def test_create_book_with_series(db_session: AsyncSession) -> None:
    series = Series(name="Hainish Cycle")
    db_session.add(series)
    await db_session.flush()

    book = Book(
        title="The Left Hand of Darkness",
        series_id=series.id,
        series_position=6.0,
        status="wanted",
        system_confidence=0.85,
    )
    db_session.add(book)
    await db_session.flush()

    await db_session.refresh(book)

    assert book.title == "The Left Hand of Darkness"
    assert book.series_position == 6.0
    assert book.effective_confidence == 0.85


async def test_create_edition_linked_to_book(db_session: AsyncSession) -> None:
    series = Series(name="Hainish Cycle")
    db_session.add(series)
    await db_session.flush()

    book = Book(
        title="The Dispossessed",
        series_id=series.id,
        status="wanted",
        system_confidence=0.8,
    )
    db_session.add(book)
    await db_session.flush()

    edition = Edition(
        book_id=book.id,
        isbn_13="9780061054945",
        format="paperback",
        language="en",
        system_confidence=0.75,
    )
    db_session.add(edition)
    await db_session.flush()

    await db_session.refresh(edition)

    assert edition.isbn_13 == "9780061054945"
    assert edition.effective_confidence == 0.75
    assert "9780061054945" in repr(edition)
