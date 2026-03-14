# ai/llm/router.py
from ai.llm.base import BaseLLMClient
from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)

_client: BaseLLMClient | None = None
_fallback_clients: list = []


def get_llm_client() -> BaseLLMClient:
    """Get primary LLM client (Ollama with GPT-OS 20B)"""
    global _client
    if _client is None:
        logger.info("llm.router.primary", provider="ollama", model=settings.OLLAMA_MODEL)
        from ai.llm.ollama_client import OllamaClient
        _client = OllamaClient()
    return _client


def get_fallback_clients():
    """Get fallback clients in order: Gemini -> OpenAI -> Mock"""
    global _fallback_clients
    if not _fallback_clients:
        # First fallback: Gemini
        if settings.GEMINI_API_KEY:
            from ai.llm.gemini_client import GeminiClient
            _fallback_clients.append(("gemini", GeminiClient()))
            logger.info("llm.router.fallback.available", provider="gemini", order=1)
        else:
            logger.warning("Gemini not configured - skipping fallback")
        
        # Second fallback: OpenAI
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.startswith("sk-"):
            from ai.llm.openai_client import OpenAIClient
            _fallback_clients.append(("openai", OpenAIClient()))
            logger.info("llm.router.fallback.available", provider="openai", order=2)
        else:
            logger.warning("OpenAI not configured - skipping fallback")
        
        # Final fallback: Mock (always available)
        from ai.llm.mock_client import MockLLMClient
        _fallback_clients.append(("mock", MockLLMClient()))
        logger.info("llm.router.fallback.available", provider="mock", order=3)
    
    return _fallback_clients


def reset_client():
    """Force re-initialization (useful for testing)."""
    global _client, _fallback_clients
    _client = None
    _fallback_clients = []