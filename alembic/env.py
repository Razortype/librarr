from __future__ import annotations

import asyncio
from logging.config import fileConfig
from typing import Any

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Import all models so their tables are registered with Base.metadata
import app.models.activity_log  # noqa: F401
import app.models.associations  # noqa: F401
import app.models.author  # noqa: F401
import app.models.book  # noqa: F401
import app.models.download  # noqa: F401
import app.models.edition  # noqa: F401
import app.models.grab  # noqa: F401
import app.models.integration_config  # noqa: F401
import app.models.metadata_cache  # noqa: F401
import app.models.quality_profile  # noqa: F401
import app.models.series  # noqa: F401
import app.models.setting  # noqa: F401
from alembic import context
from app.core.config import settings
from app.models.base import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata

_EXCLUDED_COLUMNS = {"effective_confidence"}


def include_object(object: Any, name: str, type_: str, reflected: bool, compare_to: Any) -> bool:
    if type_ == "column" and name in _EXCLUDED_COLUMNS:
        return False
    return True


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
