from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MetadataCache(Base):
    __tablename__ = "metadata_cache"

    __table_args__ = (Index("ix_metadata_cache_expires_at", "expires_at"),)

    external_id: Mapped[str] = mapped_column(String, primary_key=True)
    entity_type: Mapped[str] = mapped_column(
        Enum(
            "author",
            "book",
            "edition",
            "series",
            name="cacheentitytype",
            native_enum=True,
        ),
        primary_key=True,
    )
    data: Mapped[dict] = mapped_column(JSON, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def __repr__(self) -> str:
        return f"<MetadataCache external_id={self.external_id!r} entity_type={self.entity_type!r}>"
