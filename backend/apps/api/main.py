# apps/api/main.py
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from apps.api.lifespan import lifespan
from apps.api.routes import api_router
from core.config import settings
import time


def create_app() -> FastAPI:
    app = FastAPI(
        title="ContractIQ API",
        description="AI-powered contract analysis platform",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include all routes
    app.include_router(api_router)

    @app.get("/")
    async def root():
        return {
            "service": "ContractIQ API",
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs",
        }

    @app.get("/health")
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

    @app.get("/api/v1/llm/status")
    async def llm_status():
        """Get current LLM provider status and fallback chain"""
        from ai.llm.router import get_llm_client, get_fallback_clients
        
        primary = get_llm_client()
        fallbacks = get_fallback_clients()
        
        return {
            "primary": {
                "provider": primary.provider_name,
                "model": primary.model_name,
                "configured": True
            },
            "fallback_chain": [
                {
                    "provider": provider,
                    "model": client.model_name,
                    "configured": True
                }
                for provider, client in fallbacks
            ],
            "ollama": {
                "configured": True,
                "model": settings.OLLAMA_MODEL,
                "cloud": settings.OLLAMA_IS_CLOUD,
                "api_key_set": bool(settings.OLLAMA_API_KEY)
            },
            "gemini": {
                "configured": bool(settings.GEMINI_API_KEY),
                "model": settings.GEMINI_MODEL
            },
            "openai": {
                "configured": bool(settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.startswith("sk-")),
                "model": settings.OPENAI_MODEL
            }
        }

    return app


app = create_app()