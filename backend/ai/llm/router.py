# ai/llm/router.py
"""
LLM provider selection.

Primary provider = settings.LLM_PROVIDER (ollama | gemini | openai | mock).
Fallback chain   = every OTHER configured provider in the order
                   ollama → gemini → openai, then mock (always last).

Previously LLM_PROVIDER was ignored and Ollama was always primary, so
LLM_PROVIDER=mock (the .env.example default) still hit ollama.com on every
upload and waited for a 401 before falling back.
"""
import threading

from ai.llm.base import BaseLLMClient
from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)

_lock = threading.Lock()
_client: BaseLLMClient | None = None
_fallback_clients: list[tuple[str, BaseLLMClient]] | None = None

_ORDER = ("ollama", "gemini", "openai")


def _is_configured(provider: str) -> bool:
    if provider == "ollama":
        # Local Ollama needs no key; Ollama Cloud does
        return (not settings.OLLAMA_IS_CLOUD) or bool(settings.OLLAMA_API_KEY)
    if provider == "gemini":
        return bool(settings.GEMINI_API_KEY)
    if provider == "openai":
        return bool(settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.startswith("sk-"))
    return provider == "mock"


def _build(provider: str) -> BaseLLMClient:
    if provider == "ollama":
        from ai.llm.ollama_client import OllamaClient
        return OllamaClient()
    if provider == "gemini":
        from ai.llm.gemini_client import GeminiClient
        return GeminiClient()
    if provider == "openai":
        from ai.llm.openai_client import OpenAIClient
        return OpenAIClient()
    from ai.llm.mock_client import MockLLMClient
    return MockLLMClient()


def _primary_name() -> str:
    name = (settings.LLM_PROVIDER or "mock").strip().lower()
    if name not in (*_ORDER, "mock"):
        logger.warning(f"llm.router.unknown_provider value={name} — using mock")
        return "mock"
    if not _is_configured(name):
        logger.warning(f"llm.router.primary_not_configured provider={name} — using mock")
        return "mock"
    return name


def get_llm_client() -> BaseLLMClient:
    global _client
    with _lock:
        if _client is None:
            _client = _build(_primary_name())
            logger.info(
                f"llm.router.primary provider={_client.provider_name} model={_client.model_name}"
            )
        return _client


def get_fallback_clients() -> list[tuple[str, BaseLLMClient]]:
    global _fallback_clients
    with _lock:
        if _fallback_clients is not None:
            return _fallback_clients

        primary = _primary_name()
        chain: list[tuple[str, BaseLLMClient]] = []
        for name in _ORDER:
            if name != primary and _is_configured(name):
                chain.append((name, _build(name)))
        if primary != "mock":
            chain.append(("mock", _build("mock")))

        logger.info(f"llm.router.fallbacks chain={[n for n, _ in chain]}")
        _fallback_clients = chain
        return _fallback_clients


def reset_client():
    global _client, _fallback_clients
    with _lock:
        _client = None
        _fallback_clients = None