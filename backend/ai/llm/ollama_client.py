# ai/llm/ollama_client.py
import httpx
from ai.llm.base import BaseLLMClient
from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)


class OllamaClient(BaseLLMClient):
    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return settings.OLLAMA_MODEL

    def _endpoints(self) -> list[str]:
        """Return candidate URLs to try, in order."""
        base = settings.OLLAMA_BASE_URL.rstrip("/")
        if settings.OLLAMA_IS_CLOUD:
            # Ollama Cloud speaks the OpenAI-compatible API at /v1/chat/completions
            # and also exposes a native /api/chat endpoint. Try both.
            return [
                f"{base}/v1/chat/completions",
                f"{base}/api/chat",
            ]
        return [
            f"{base}/api/chat",
            f"{base}/api/generate",
        ]

    async def complete(self, system: str, user: str, json_mode: bool = True) -> str:
        headers = {"Content-Type": "application/json"}
        if settings.OLLAMA_API_KEY:
            headers["Authorization"] = f"Bearer {settings.OLLAMA_API_KEY}"

        last_error: Exception | None = None

        for url in self._endpoints():
            try:
                if url.endswith("/v1/chat/completions"):
                    payload = {
                        "model": settings.OLLAMA_MODEL,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": user},
                        ],
                        "temperature": 0.2,
                        "stream": False,
                    }
                    if json_mode:
                        payload["response_format"] = {"type": "json_object"}
                elif url.endswith("/api/chat"):
                    payload = {
                        "model": settings.OLLAMA_MODEL,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": user},
                        ],
                        "stream": False,
                        "options": {"temperature": 0.2, "num_predict": 4000},
                    }
                    if json_mode:
                        payload["format"] = "json"
                else:  # /api/generate (local only)
                    payload = {
                        "model": settings.OLLAMA_MODEL,
                        "prompt": f"{system}\n\n{user}",
                        "stream": False,
                        "options": {"temperature": 0.2, "num_predict": 4000},
                    }
                    if json_mode:
                        payload["format"] = "json"

                logger.info(f"ollama.request url={url} model={settings.OLLAMA_MODEL}")
                async with httpx.AsyncClient(timeout=180) as client:
                    resp = await client.post(url, json=payload, headers=headers)

                    if resp.status_code == 401:
                        raise Exception("Ollama authentication failed: invalid API key")
                    if resp.status_code == 404:
                        # Try next endpoint (may be wrong path for this provider)
                        last_error = Exception(f"404 on {url}")
                        logger.warning(f"ollama.404 url={url} — trying next endpoint")
                        continue
                    resp.raise_for_status()
                    data = resp.json()

                # OpenAI-compatible shape
                if "choices" in data and data["choices"]:
                    return data["choices"][0]["message"]["content"]
                # Native /api/chat shape
                if "message" in data and "content" in data["message"]:
                    return data["message"]["content"]
                # Native /api/generate shape
                if "response" in data:
                    return data["response"]

                raise Exception(f"Unexpected Ollama response shape: {list(data.keys())}")

            except httpx.TimeoutException as e:
                last_error = e
                logger.error(f"ollama.timeout url={url}")
                continue
            except httpx.HTTPStatusError as e:
                last_error = e
                logger.error(f"ollama.http_error url={url} status={e.response.status_code}")
                continue
            except Exception as e:
                last_error = e
                logger.error(f"ollama.error url={url} error={str(e)}")
                continue

        raise Exception(f"All Ollama endpoints failed. Last error: {last_error}")