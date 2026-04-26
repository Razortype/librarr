from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, UUID, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, ConfidenceMixin, uuid7_pk

if TYPE_CHECKING:
    from app.models.book import Book
    from app.models.download import Download


class Edition(ConfidenceMixin, Base):
    __tablename__ = "editions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7_pk)
    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
    )
    isbn_10: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)
    isbn_13: Mapped[str | None] = mapped_column(String(13), nullable=True, index=True)
    asin: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)
    format: Mapped[str | None] = mapped_column(
        Enum(
            "hardcover",
            "paperback",
            "ebook",
            "audiobook",
            "large_print",
            "mass_market",
            name="editionformat",
            native_enum=True,
        ),
        nullable=True,
    )
    language: Mapped[str | None] = mapped_column(String(8), nullable=True)
    publisher: Mapped[str | None] = mapped_column(String, nullable=True)
    publication_date: Mapped[date | None] = mapped_column(nullable=True)
    page_count: Mapped[int | None] = mapped_column(nullable=True)
    audio_duration_seconds: Mapped[int | None] = mapped_column(nullable=True)
    narrators: Mapped[list | None] = mapped_column(JSON, nullable=True)
    translators: Mapped[list | None] = mapped_column(JSON, nullable=True)
    cover_url: Mapped[str | None] = mapped_column(String, nullable=True)
    external_ids: Mapped[dict] = mapped_column(JSON, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    book: Mapped[Book] = relationship("Book", back_populates="editions")
    downloads: Mapped[list[Download]] = relationship("Download", back_populates="edition")

    def __repr__(self) -> str:
        display = self.isbn_13 or str(self.id)
        return f"<Edition id={self.id} isbn_13={display!r}>"
