"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-26

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PgEnum

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

# ---------------------------------------------------------------------------
# Enum types (Postgres native)
# ---------------------------------------------------------------------------

# PgEnum with create_type=False: we manage DDL explicitly via op.execute() DO blocks.
# sa.Enum silently ignores create_type=False (not a supported kwarg); PgEnum stores it
# correctly so _can_create_type() returns early and op.create_table() does not also
# emit CREATE TYPE after the DO block already ran.
bookstatus = PgEnum(
    "wanted",
    "monitored",
    "unmonitored",
    "archived",
    name="bookstatus",
    create_type=False,
)
authorrole = PgEnum(
    "primary",
    "co_author",
    "contributor",
    "translator",
    "illustrator",
    name="authorrole",
    create_type=False,
)
editionformat = PgEnum(
    "hardcover",
    "paperback",
    "ebook",
    "audiobook",
    "large_print",
    "mass_market",
    name="editionformat",
    create_type=False,
)
downloadstatus = PgEnum(
    "queued",
    "searching",
    "downloading",
    "completed",
    "failed",
    "imported",
    "cancelled",
    name="downloadstatus",
    create_type=False,
)
integrationtype = PgEnum(
    "prowlarr",
    "qbittorrent",
    "calibre",
    name="integrationtype",
    create_type=False,
)
cacheentitytype = PgEnum(
    "author",
    "book",
    "edition",
    "series",
    name="cacheentitytype",
    create_type=False,
)


def upgrade() -> None:
    """Create all tables in FK-safe order."""

    # -- series ---------------------------------------------------------------
    op.create_table(
        "series",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("external_ids", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("system_confidence", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("user_confidence", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # -- authors --------------------------------------------------------------
    op.create_table(
        "authors",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("canonical_name", sa.String(), nullable=False),
        sa.Column("sort_name", sa.String(), nullable=False),
        sa.Column("aliases", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("birth_year", sa.Integer(), nullable=True),
        sa.Column("death_year", sa.Integer(), nullable=True),
        sa.Column("external_ids", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("biography", sa.String(), nullable=True),
        sa.Column("image_url", sa.String(), nullable=True),
        sa.Column("system_confidence", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("user_confidence", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # -- books ----------------------------------------------------------------
    op.execute(
        sa.text("""
        DO $$ BEGIN
            CREATE TYPE bookstatus AS ENUM ('wanted', 'monitored', 'unmonitored', 'archived');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    )
    op.create_table(
        "books",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("original_title", sa.String(), nullable=True),
        sa.Column("original_language", sa.String(8), nullable=True),
        sa.Column("publication_year", sa.Integer(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("series_id", sa.UUID(), nullable=True),
        sa.Column("series_position", sa.Float(), nullable=True),
        sa.Column("external_ids", sa.JSON(), server_default="{}", nullable=False),
        sa.Column(
            "status",
            bookstatus,
            nullable=False,
            server_default="wanted",
        ),
        sa.Column("system_confidence", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("user_confidence", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["series_id"], ["series.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # -- book_authors ---------------------------------------------------------
    op.execute(
        sa.text("""
        DO $$ BEGIN
            CREATE TYPE authorrole AS ENUM ('primary', 'co_author', 'contributor', 'translator', 'illustrator');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    )
    op.create_table(
        "book_authors",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("book_id", sa.UUID(), nullable=False),
        sa.Column("author_id", sa.UUID(), nullable=False),
        sa.Column("role", authorrole, nullable=False),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["authors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("book_id", "author_id", "role", name="uq_book_author_role"),
    )

    # -- editions -------------------------------------------------------------
    op.execute(
        sa.text("""
        DO $$ BEGIN
            CREATE TYPE editionformat AS ENUM ('hardcover', 'paperback', 'ebook', 'audiobook', 'large_print', 'mass_market');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    )
    op.create_table(
        "editions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("book_id", sa.UUID(), nullable=False),
        sa.Column("isbn_10", sa.String(10), nullable=True),
        sa.Column("isbn_13", sa.String(13), nullable=True),
        sa.Column("asin", sa.String(), nullable=True),
        sa.Column("format", editionformat, nullable=True),
        sa.Column("language", sa.String(), nullable=True),
        sa.Column("publisher", sa.String(), nullable=True),
        sa.Column("publication_date", sa.Date(), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("audio_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("narrators", sa.JSON(), nullable=True),
        sa.Column("translators", sa.JSON(), nullable=True),
        sa.Column("cover_url", sa.String(), nullable=True),
        sa.Column("external_ids", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("system_confidence", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("user_confidence", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_editions_isbn_10", "editions", ["isbn_10"])
    op.create_index("ix_editions_isbn_13", "editions", ["isbn_13"])
    op.create_index("ix_editions_asin", "editions", ["asin"])

    # -- downloads ------------------------------------------------------------
    op.execute(
        sa.text("""
        DO $$ BEGIN
            CREATE TYPE downloadstatus AS ENUM ('queued', 'searching', 'downloading', 'completed', 'failed', 'imported', 'cancelled');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    )
    op.create_table(
        "downloads",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("edition_id", sa.UUID(), nullable=False),
        sa.Column(
            "status",
            downloadstatus,
            nullable=False,
            server_default="queued",
        ),
        sa.Column("download_client", sa.String(), nullable=False),
        sa.Column("indexer_name", sa.String(), nullable=True),
        sa.Column("release_title", sa.String(), nullable=True),
        sa.Column("external_id", sa.String(), nullable=True),
        sa.Column("quality", sa.JSON(), nullable=True),
        sa.Column("progress", sa.Float(), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["edition_id"], ["editions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_downloads_status_created_at", "downloads", ["status", "created_at"])

    # -- quality_profiles -----------------------------------------------------
    op.create_table(
        "quality_profiles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("formats", sa.JSON(), nullable=False),
        sa.Column("languages", sa.JSON(), nullable=False),
        sa.Column("min_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("max_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("allow_audiobook", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # -- settings -------------------------------------------------------------
    op.create_table(
        "settings",
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("value", sa.String(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("key"),
    )

    # -- integration_configs --------------------------------------------------
    op.execute(
        sa.text("""
        DO $$ BEGIN
            CREATE TYPE integrationtype AS ENUM ('prowlarr', 'qbittorrent', 'calibre');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    )
    op.create_table(
        "integration_configs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("type", integrationtype, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("config", sa.LargeBinary(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_test_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_test_ok", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # -- metadata_cache -------------------------------------------------------
    op.execute(
        sa.text("""
        DO $$ BEGIN
            CREATE TYPE cacheentitytype AS ENUM ('author', 'book', 'edition', 'series');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    )
    op.create_table(
        "metadata_cache",
        sa.Column("external_id", sa.String(), nullable=False),
        sa.Column("entity_type", cacheentitytype, nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("external_id", "entity_type"),
    )
    op.create_index("ix_metadata_cache_expires_at", "metadata_cache", ["expires_at"])

    # -- activity_logs --------------------------------------------------------
    op.create_table(
        "activity_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("entity_type", sa.String(), nullable=True),
        sa.Column("entity_id", sa.UUID(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Drop all tables in reverse FK order, then drop ENUM types."""

    op.drop_table("activity_logs")
    op.drop_index("ix_metadata_cache_expires_at", table_name="metadata_cache")
    op.drop_table("metadata_cache")
    op.drop_table("integration_configs")
    op.drop_table("settings")
    op.drop_table("quality_profiles")
    op.drop_index("ix_downloads_status_created_at", table_name="downloads")
    op.drop_table("downloads")
    op.drop_index("ix_editions_asin", table_name="editions")
    op.drop_index("ix_editions_isbn_13", table_name="editions")
    op.drop_index("ix_editions_isbn_10", table_name="editions")
    op.drop_table("editions")
    op.drop_table("book_authors")
    op.drop_table("books")
    op.drop_table("authors")
    op.drop_table("series")

    op.execute(sa.text("DROP TYPE IF EXISTS cacheentitytype"))
    op.execute(sa.text("DROP TYPE IF EXISTS integrationtype"))
    op.execute(sa.text("DROP TYPE IF EXISTS downloadstatus"))
    op.execute(sa.text("DROP TYPE IF EXISTS editionformat"))
    op.execute(sa.text("DROP TYPE IF EXISTS authorrole"))
    op.execute(sa.text("DROP TYPE IF EXISTS bookstatus"))
