from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, UUID, Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, uuid7_pk


class QualityProfile(Base):
    __tablename__ = "quality_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7_pk)
    name: Mapped[str] = mapped_column(String, nullable=False)
    formats: Mapped[list] = mapped_column(JSON, nullable=False)
    languages: Mapped[list] = mapped_column(JSON, nullable=False)
    min_size_bytes: Mapped[int | None] = mapped_column(nullable=True)
    max_size_bytes: Mapped[int | None] = mapped_column(nullable=True)
    allow_audiobook: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<QualityProfile id={self.id} name={self.name!r}>"
