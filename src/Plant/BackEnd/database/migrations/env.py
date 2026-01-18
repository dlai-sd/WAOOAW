"""Alembic environment for Plant database migrations (async, autogenerate enabled)."""

from __future__ import annotations

import asyncio
from logging.config import fileConfig
from typing import Optional

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine

from core.database import Base
from core.config import settings

# Import models so metadata is populated for autogenerate
import models.base_entity  # noqa: F401
import models.skill  # noqa: F401
import models.job_role  # noqa: F401
import models.team  # noqa: F401


config = context.config

# Override sqlalchemy.url from settings, but use sync driver for migrations
database_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (supports async engines)."""

    connectable = config.attributes.get("connection")
    if connectable is None:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            future=True,
        )

    if isinstance(connectable, AsyncEngine):
        async def process_migrations() -> None:
            async with connectable.connect() as connection:
                await connection.run_sync(do_run_migrations)

        asyncio.run(process_migrations())
    else:
        with connectable.connect() as connection:
            do_run_migrations(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
