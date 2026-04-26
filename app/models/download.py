from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, UUID, DateTime, Enum, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, uuid7_pk

if TYPE_CHECKING:
    from app.models.edition import Edition


class Download(Base):
    __tablename__ = "downloads"

    __table_args__ = (
        Index("ix_downloads_status_created_at", "status", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7_pk)
    edition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("editions.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Enum(
            "queued",
            "searching",
            "downloading",
            "completed",
            "failed",
            "imported",
            "cancelled",
            name="downloadstatus",
            native_enum=True,
        ),
        default="queued",
        nullable=False,
    )
    download_client: Mapped[str] = mapped_column(String, nullable=False)
    indexer_name: Mapped[str | None] = mapped_column(String, nullable=True)
    release_title: Mapped[str | None] = mapped_column(String, nullable=True)
    external_id: Mapped[str | None] = mapped_column(String, nullable=True)
    quality: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    progress: Mapped[float | None] = mapped_column(nullable=True)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    imported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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
    edition: Mapped[Edition] = relationship("Edition", back_populates="downloads")

    def __repr__(self) -> str:
        return f"<Download id={self.id} status={self.status!r}>"
