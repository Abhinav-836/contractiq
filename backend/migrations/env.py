"""
Alembic environment.

Two ways in:
  * App startup (db/migrate.py) passes an open connection in
    config.attributes["connection"].
  * The `alembic` CLI builds its own async engine from DATABASE_URL.
"""
import asyncio

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from core.config import settings
from db.base import Base
from db.models import import_all_models

import_all_models()
target_metadata = Base.metadata


def _configure(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # SQLite can't ALTER most things in place; batch mode rebuilds the table.
        render_as_batch=connection.dialect.name == "sqlite",
        compare_type=True,
    )


def _run(connection) -> None:
    _configure(connection)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_offline() -> None:
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


async def _run_async() -> None:
    from db.session import _engine_kwargs

    kwargs = _engine_kwargs()
    kwargs.pop("pool_size", None)
    kwargs.pop("max_overflow", None)
    engine = create_async_engine(settings.DATABASE_URL, **kwargs)
    async with engine.connect() as conn:
        await conn.run_sync(_run)
        await conn.commit()
    await engine.dispose()


def run_migrations_online() -> None:
    connection = context.config.attributes.get("connection")
    if connection is not None:
        _run(connection)
    else:
        asyncio.run(_run_async())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
