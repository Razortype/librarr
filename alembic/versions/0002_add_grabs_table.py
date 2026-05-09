"""add grabs table

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-09
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PgEnum

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

grabstatus = PgEnum("grabbed", name="grabstatus", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()

    if bind.dialect.name == "postgresql":
        # ADD VALUE cannot run inside a transaction; autocommit_block handles the
        # commit/begin around this single statement.
        with op.get_context().autocommit_block():
            op.execute(sa.text("ALTER TYPE bookstatus ADD VALUE IF NOT EXISTS 'grabbed'"))

        op.execute(
            sa.text("""
            DO $$ BEGIN
                CREATE TYPE grabstatus AS ENUM ('grabbed');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """)
        )

    op.create_table(
        "grabs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("book_id", sa.UUID(), nullable=False),
        sa.Column("release_guid", sa.String(512), nullable=False),
        sa.Column("release_title", sa.String(1024), nullable=False),
        sa.Column("indexer_name", sa.String(255), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("qbit_hash", sa.String(40), nullable=False),
        sa.Column(
            "status",
            grabstatus,
            nullable=False,
            server_default="grabbed",
        ),
        sa.Column(
            "grabbed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("book_id", "release_guid", name="uq_grabs_book_release"),
    )
    op.create_index("ix_grabs_book_id", "grabs", ["book_id"])
    op.create_index("ix_grabs_qbit_hash", "grabs", ["qbit_hash"])


def downgrade() -> None:
    op.drop_index("ix_grabs_qbit_hash", table_name="grabs")
    op.drop_index("ix_grabs_book_id", table_name="grabs")
    op.drop_table("grabs")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(sa.text("DROP TYPE IF EXISTS grabstatus"))
        # Note: removing a value from a Postgres enum is not supported; 'grabbed'
        # remains in bookstatus after downgrade but causes no functional harm.
