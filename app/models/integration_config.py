from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import UUID, Boolean, DateTime, Enum, LargeBinary, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, uuid7_pk


class IntegrationConfig(Base):
    __tablename__ = "integration_configs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7_pk)
    type: Mapped[str] = mapped_column(
        Enum(
            "prowlarr",
            "qbittorrent",
            "calibre",
            name="integrationtype",
            native_enum=True,
        ),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    config: Mapped[bytes] = mapped_column(
        LargeBinary, nullable=False
    )  # TODO: encrypt with Fernet before write, decrypt after read
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_test_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_test_ok: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
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
        return f"<IntegrationConfig id={self.id} type={self.type!r} name={self.name!r}>"
