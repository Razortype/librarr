from __future__ import annotations

import uuid

import uuid_utils
from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, column_property, declared_attr, mapped_column


class Base(DeclarativeBase):
    pass


def uuid7_pk() -> uuid.UUID:
    return uuid_utils.uuid7()


class ConfidenceMixin:
    system_confidence: Mapped[float] = mapped_column(default=0.0)
    user_confidence: Mapped[float | None] = mapped_column(nullable=True, default=None)

    @declared_attr
    def effective_confidence(cls) -> Mapped[float]:
        return column_property(func.coalesce(cls.user_confidence, cls.system_confidence))
