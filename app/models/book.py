from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, UUID, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from app.models.associations import book_authors_table
from app.models.base import Base, uuid7_pk

if TYPE_CHECKING:
    from app.models.author import Author
    from app.models.edition import Edition
    from app.models.series import Series


class Book(Base):
    __tablename__ = "books"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7_pk)
    title: Mapped[str] = mapped_column(String, nullable=False)
    original_title: Mapped[str | None] = mapped_column(String, nullable=True)
    original_language: Mapped[str | None] = mapped_column(String(8), nullable=True)
    publication_year: Mapped[int | None] = mapped_column(nullable=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    series_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("series.id", ondelete="SET NULL"),
        nullable=True,
    )
    series_position: Mapped[float | None] = mapped_column(nullable=True)
    external_ids: Mapped[dict] = mapped_column(JSON, server_default="{}")
    status: Mapped[str] = mapped_column(
        Enum(
            "wanted",
            "monitored",
            "unmonitored",
            "archived",
            name="bookstatus",
            native_enum=True,
        ),
        default="wanted",
        nullable=False,
    )
    system_confidence: Mapped[float] = mapped_column(default=0.0)
    user_confidence: Mapped[float | None] = mapped_column(nullable=True, default=None)
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
    series: Mapped[Series | None] = relationship("Series", back_populates="books")
    authors: Mapped[list[Author]] = relationship(
        "Author",
        secondary=book_authors_table,
        back_populates="books",
    )
    editions: Mapped[list[Edition]] = relationship("Edition", back_populates="book")

    def __repr__(self) -> str:
        return f"<Book id={self.id} title={self.title!r}>"


Book.effective_confidence = column_property(  # type: ignore[attr-defined]
    func.coalesce(Book.user_confidence, Book.system_confidence)
)
