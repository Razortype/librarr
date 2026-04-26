from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, UUID, DateTime, String, func
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from app.models.base import Base, uuid7_pk

if TYPE_CHECKING:
    from app.models.book import Book


class Series(Base):
    __tablename__ = "series"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7_pk)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    external_ids: Mapped[dict] = mapped_column(JSON, server_default="{}")
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
    books: Mapped[list[Book]] = relationship("Book", back_populates="series")

    def __repr__(self) -> str:
        return f"<Series id={self.id} name={self.name!r}>"


# column_property requires the table to be fully defined, so we attach it after the class
Series.effective_confidence = column_property(  # type: ignore[attr-defined]
    func.coalesce(Series.user_confidence, Series.system_confidence)
)
