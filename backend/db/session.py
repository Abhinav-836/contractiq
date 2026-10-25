# db/session.py
import ssl
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)


def _engine_kwargs() -> dict:
    """
    SQLite (aiosqlite) and Postgres (asyncpg) accept different connect args.
    Passing asyncpg's `ssl` / `statement_cache_size` to aiosqlite crashes startup
    with: TypeError: Connection() got an unexpected keyword argument 'ssl'.
    """
    if settings.is_sqlite:
        return {
            "echo": False,
            "connect_args": {"check_same_thread": False},
        }

    kwargs = {
        "echo": False,          # SQL echo floods prod logs and leaks data — keep off
        "pool_size": 5,         # Neon free tier has connection limits — keep this small
        "max_overflow": 10,
        "pool_pre_ping": True,  # drops dead connections before use
        "pool_recycle": 300,    # Neon kills idle conns
        "connect_args": {"statement_cache_size": 0},  # PgBouncer-safe
    }
    # Only force SSL for remote databases (Neon etc.), not a local Postgres
    if "localhost" not in settings.DATABASE_URL and "127.0.0.1" not in settings.DATABASE_URL:
        kwargs["connect_args"]["ssl"] = ssl.create_default_context()
    return kwargs


engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs())

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """Create all tables on startup."""
    from db.base import Base
    # Import all models so they register with Base.metadata
    import modules.users.models        # noqa: F401
    import modules.contracts.models    # noqa: F401
    import modules.analysis.models     # noqa: F401
    import modules.obligations.models  # noqa: F401
    import modules.alerts.models       # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database.initialized")


async def close_db():
    await engine.dispose()
    logger.info("database.connections_closed")