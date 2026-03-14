from contextlib import asynccontextmanager
from fastapi import FastAPI
from db.session import init_db
from core.logger import get_logger, setup_logging
from core.config import settings

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("startup.begin", env=settings.APP_ENV, provider=settings.effective_llm_provider)

    await init_db()
    logger.info("startup.db_ready")

    print(f"""
╔══════════════════════════════════════════════╗
║         ContractIQ Backend v1.0.0            ║
╠══════════════════════════════════════════════╣
║  API:      http://localhost:8000             ║
║  Docs:     http://localhost:8000/docs        ║
║  Health:   http://localhost:8000/api/v1/health║
║  LLM:      {settings.effective_llm_provider:<34}║
╚══════════════════════════════════════════════╝
""")

    yield

    logger.info("shutdown.complete")
