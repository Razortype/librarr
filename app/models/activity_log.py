from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, UUID, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, uuid7_pk


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7_pk)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String, nullable=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<ActivityLog id={self.id} event_type={self.event_type!r}>"
