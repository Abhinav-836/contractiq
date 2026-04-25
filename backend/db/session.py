# db/session.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)

# Configure engine based on database type
if "postgresql" in settings.DATABASE_URL:
    # PostgreSQL specific settings with connection pooling
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
    )
elif "sqlite" in settings.DATABASE_URL:
    # SQLite settings (no pooling)
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False},
    )
else:
    # Default fallback
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
    )

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


from typing import AsyncGenerator

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
    # Import all models so they're registered
    import modules.contracts.models
    import modules.analysis.models
    import modules.obligations.models
    import modules.alerts.models
    import modules.users.models

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database.initialized")


async def close_db():
    """Close database connections on shutdown."""
    await engine.dispose()
    logger.info("database.connections_closed")