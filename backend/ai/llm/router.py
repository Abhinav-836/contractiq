# ai/llm/router.py
import threading

from ai.llm.base import BaseLLMClient
from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)

_lock = threading.Lock()
_client: BaseLLMClient | None = None
_fallback_clients: list[tuple[str, BaseLLMClient]] = []


def get_llm_client() -> BaseLLMClient:
    """Primary: Ollama Cloud (GPT-OSS 20B)."""
    global _client
    with _lock:
        if _client is None:
            from ai.llm.ollama_client import OllamaClient
            _client = OllamaClient()
            logger.info(
                f"llm.router.primary provider={_client.provider_name} model={_client.model_name}"
            )
        return _client


def get_fallback_clients() -> list[tuple[str, BaseLLMClient]]:
    """Fallback order: Gemini → OpenAI → Mock."""
    global _fallback_clients
    with _lock:
        if _fallback_clients:
            return _fallback_clients

        chain: list[tuple[str, BaseLLMClient]] = []

        if settings.GEMINI_API_KEY:
            from ai.llm.gemini_client import GeminiClient
            chain.append(("gemini", GeminiClient()))
            logger.info("llm.router.fallback provider=gemini order=1")
        else:
            logger.warning("llm.router.fallback gemini_not_configured")

        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.startswith("sk-"):
            from ai.llm.openai_client import OpenAIClient
            chain.append(("openai", OpenAIClient()))
            logger.info("llm.router.fallback provider=openai order=2")
        else:
            logger.warning("llm.router.fallback openai_not_configured")

        from ai.llm.mock_client import MockLLMClient
        chain.append(("mock", MockLLMClient()))
        logger.info("llm.router.fallback provider=mock order=3")

        _fallback_clients = chain
        return _fallback_clients


def reset_client():
    global _client, _fallback_clients
    with _lock:
        _client = None
        _fallback_clients = []