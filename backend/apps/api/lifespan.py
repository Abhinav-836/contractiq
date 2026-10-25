# apps/api/lifespan.py
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import select, func, text, update

from core.config import settings
from core.logger import get_logger, setup_logging
from db.session import init_db, close_db

logger = get_logger(__name__)


async def validate_database_connection() -> None:
    from db.session import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        await db.execute(text("SELECT 1"))
    logger.info("database.connection_verified")


async def recover_interrupted_analyses() -> None:
    """
    Analysis runs as an in-process background task. If the server restarts mid-run
    (Render free tier sleeps/redeploys often), the contract stays "processing"
    forever and the UI spins indefinitely. Mark those as failed so the user can retry.
    """
    from db.session import AsyncSessionLocal
    from modules.contracts.models import Contract

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            update(Contract)
            .where(Contract.status == "processing")
            .values(status="failed")
            .execution_options(synchronize_session=False)
        )
        await db.commit()
        if result.rowcount:
            logger.warning(f"startup.recovered_stuck_contracts count={result.rowcount}")


async def ensure_default_user() -> None:
    """
    Opt-in only (SEED_DEV_USER=true). It used to run whenever APP_ENV != production,
    and the deployed backend runs with APP_ENV=development — so a public account with
    a password published in the source code was created on the live database.
    """
    if not settings.SEED_DEV_USER or settings.APP_ENV == "production":
        return
    try:
        from db.session import AsyncSessionLocal
        from modules.users.models import User
        from modules.users.repository import UserRepository

        async with AsyncSessionLocal() as db:
            count = (await db.execute(select(func.count()).select_from(User))).scalar()
            if count:
                return
            await UserRepository(db).create(
                email="test@example.com", name="Test User", password="test1234"
            )
            await db.commit()
            logger.warning("users.dev_test_user_created email=test@example.com")
    except Exception as e:
        logger.error(f"users.ensure_default_failed error={e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info(f"startup.begin env={settings.APP_ENV} llm_provider={settings.effective_llm_provider}")

    await validate_database_connection()
    await init_db()
    await recover_interrupted_analyses()
    await ensure_default_user()

    logger.info(
        f"startup.ready db={'sqlite' if settings.is_sqlite else 'postgres'} "
        f"origins={settings.allowed_origins_list}"
    )

    yield

    await close_db()
    logger.info("shutdown.complete")