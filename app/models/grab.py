from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    UUID,
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, uuid7_pk

if TYPE_CHECKING:
    from app.models.book import Book


class Grab(Base):
    __tablename__ = "grabs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7_pk)
    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
    )
    release_guid: Mapped[str] = mapped_column(String(512), nullable=False)
    release_title: Mapped[str] = mapped_column(String(1024), nullable=False)
    indexer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    qbit_hash: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(
            "grabbed",
            name="grabstatus",
            native_enum=True,
        ),
        default="grabbed",
        nullable=False,
    )
    grabbed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    book: Mapped[Book] = relationship("Book", back_populates="grabs")

    __table_args__ = (
        UniqueConstraint("book_id", "release_guid", name="uq_grabs_book_release"),
        Index("ix_grabs_book_id", "book_id"),
        Index("ix_grabs_qbit_hash", "qbit_hash"),
    )

    def __repr__(self) -> str:
        return f"<Grab id={self.id} book_id={self.book_id} hash={self.qbit_hash!r}>"
