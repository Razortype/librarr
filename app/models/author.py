from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, UUID, DateTime, String, func
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from app.models.associations import book_authors_table
from app.models.base import Base, uuid7_pk

if TYPE_CHECKING:
    from app.models.book import Book


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7_pk)
    canonical_name: Mapped[str] = mapped_column(String, nullable=False)
    sort_name: Mapped[str] = mapped_column(String, nullable=False)
    aliases: Mapped[list] = mapped_column(JSON, server_default="[]")
    birth_year: Mapped[int | None] = mapped_column(nullable=True)
    death_year: Mapped[int | None] = mapped_column(nullable=True)
    external_ids: Mapped[dict] = mapped_column(JSON, server_default="{}")
    biography: Mapped[str | None] = mapped_column(String, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)
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
    books: Mapped[list[Book]] = relationship(
        "Book",
        secondary=book_authors_table,
        back_populates="authors",
    )

    def __repr__(self) -> str:
        return f"<Author id={self.id} canonical_name={self.canonical_name!r}>"


Author.effective_confidence = column_property(  # type: ignore[attr-defined]
    func.coalesce(Author.user_confidence, Author.system_confidence)
)
