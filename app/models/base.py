from __future__ import annotations

import uuid

import uuid_utils
from sqlalchemy.orm import DeclarativeBase, MappedColumn  # noqa: F401


class Base(DeclarativeBase):
    pass


def uuid7_pk() -> uuid.UUID:
    return uuid_utils.uuid7()
