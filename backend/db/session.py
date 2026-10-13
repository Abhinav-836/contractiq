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

# Neon requires SSL. Create a default context.
_ssl_ctx = ssl.create_default_context()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=5,           # Neon free tier has connection limits — keep this small
    max_overflow=10,
    pool_pre_ping=True,    # drops dead connections before use
    pool_recycle=300,      # recycle every 5 min — Neon kills idle conns
    connect_args={"ssl": _ssl_ctx, "statement_cache_size": 0},  # PgBouncer-safe
)

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
        finally:
            await session.close()


async def init_db():
    """Create all tables on startup."""
    from db.base import Base
    # Import all models so they register with Base.metadata
    import modules.contracts.models  # noqa: F401
    import modules.analysis.models   # noqa: F401
    import modules.obligations.models  # noqa: F401
    import modules.alerts.models     # noqa: F401
    import modules.users.models      # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database.initialized")


async def close_db():
    await engine.dispose()
    logger.info("database.connections_closed")