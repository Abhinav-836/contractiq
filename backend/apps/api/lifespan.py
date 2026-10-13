# apps/api/lifespan.py
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import select, func, text

from core.config import settings
from core.logger import get_logger, setup_logging
from db.session import init_db, close_db

logger = get_logger(__name__)


async def validate_database_connection() -> bool:
    from db.session import AsyncSessionLocal
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        logger.info("database.connection_verified")
        return True
    except Exception as e:
        logger.error(f"database.connection_failed error={e}")
        raise


async def ensure_default_user():
    """Dev-only: create default test user if DB is empty."""
    if settings.APP_ENV == "production":
        return

    try:
        from db.session import AsyncSessionLocal
        from modules.users.models import User
        from modules.users.repository import UserRepository

        async with AsyncSessionLocal() as db:
            count = (await db.execute(select(func.count()).select_from(User))).scalar()
            if count and count > 0:
                logger.info(f"users.existing count={count}")
                return

            logger.warning("users.none_found — creating dev test user")
            repo = UserRepository(db)
            await repo.create(
                email="test@example.com",
                name="Test User",
                password="test1234",
            )
            await db.commit()

            logger.info("users.test_user_created email=test@example.com")
            print("\n" + "=" * 60)
            print("DEV TEST USER: test@example.com / test1234")
            print("=" * 60 + "\n")
    except Exception as e:
        logger.error(f"users.ensure_default_failed error={e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info(
        f"startup.begin env={settings.APP_ENV} llm_provider={settings.effective_llm_provider}"
    )

    await validate_database_connection()
    await init_db()
    logger.info("startup.db_ready")

    await ensure_default_user()

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                  ContractIQ Backend v1.0.0                   ║
╠══════════════════════════════════════════════════════════════╣
║  Environment:  {settings.APP_ENV:<45}║
║  Docs:         /docs{40: <45}║
║  Health:       /api/v1/health{40: <45}║
║  LLM Provider: {settings.effective_llm_provider:<45}║
║  DB:           {'SQLite' if settings.is_sqlite else 'PostgreSQL':<45}║
╚══════════════════════════════════════════════════════════════╝
""")

    yield

    await close_db()
    logger.info("shutdown.complete")