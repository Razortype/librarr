from __future__ import annotations

from sqlalchemy import (
    UUID,
    Column,
    Enum,
    ForeignKey,
    Integer,
    Table,
    UniqueConstraint,
)

from app.models.base import Base, uuid7_pk

book_authors_table = Table(
    "book_authors",
    Base.metadata,
    Column(
        "id",
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7_pk,
    ),
    Column(
        "book_id",
        UUID(as_uuid=True),
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "author_id",
        UUID(as_uuid=True),
        ForeignKey("authors.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "role",
        Enum(
            "primary",
            "co_author",
            "contributor",
            "translator",
            "illustrator",
            name="authorrole",
            native_enum=True,
        ),
        nullable=False,
    ),
    Column("position", Integer, nullable=True),
    UniqueConstraint("book_id", "author_id", "role", name="uq_book_author_role"),
)
