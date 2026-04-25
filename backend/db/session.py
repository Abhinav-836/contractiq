# db/session.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)

# PostgreSQL connection configuration
connect_args = {}
if "postgresql" in settings.DATABASE_URL:
    # PostgreSQL specific settings
    connect_args = {
        "server_settings": {
            "jit": "off",  # Disable JIT for better performance
            "statement_timeout": "30000",  # 30 second timeout
        }
    }
elif "sqlite" in settings.DATABASE_URL:
    # SQLite settings (for local development)
    connect_args = {
        "check_same_thread": False,
        "timeout": 30,
    }

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args=connect_args,
    pool_size=20,  # Connection pool size for PostgreSQL
    max_overflow=10,  # Extra connections beyond pool_size
    pool_pre_ping=True,  # Verify connections before using
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
        # For production, you should use Alembic migrations
        # This is only for development/quick start
        if settings.APP_ENV != "production":
            await conn.run_sync(Base.metadata.create_all)
            logger.info("database.tables_created")
        else:
            logger.info("database.production_use_migrations")
    
    logger.info("database.initialized")


async def close_db():
    """Close database connections on shutdown."""
    await engine.dispose()
    logger.info("database.connections_closed")