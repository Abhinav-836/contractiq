# apps/api/routes.py
from fastapi import APIRouter, Response
from fastapi import APIRouter, Depends
from modules.users.api import router as users_router
from modules.contracts.api import router as contracts_router
from modules.analysis.api import router as analysis_router
from modules.obligations.api import router as obligations_router
from modules.alerts.api import router as alerts_router
from core.config import settings
import time

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(users_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(contracts_router, prefix="/contracts", tags=["Contracts"])
api_router.include_router(analysis_router, prefix="/analysis", tags=["Analysis"])
api_router.include_router(obligations_router, prefix="/obligations", tags=["Obligations"])
api_router.include_router(alerts_router, prefix="/alerts", tags=["Alerts"])


@api_router.get("/health")
async def health_check(response: Response):
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "contractiq-backend",
        "version": "1.0.0",
        "environment": settings.APP_ENV,
        "llm_provider": settings.effective_llm_provider,
        "llm_model": settings.OLLAMA_MODEL if settings.LLM_PROVIDER == "ollama" else "N/A"
    }