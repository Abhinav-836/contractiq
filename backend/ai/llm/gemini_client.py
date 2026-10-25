import json
import re

import httpx

from ai.llm.base import BaseLLMClient
from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)


class GeminiClient(BaseLLMClient):
    BASE = "https://generativelanguage.googleapis.com/v1beta/models"

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return settings.GEMINI_MODEL

    async def complete(self, system: str, user: str, json_mode: bool = True) -> str:
        model = self.model_name.replace("models/", "")
        # Key goes in a header, not the query string: httpx logs every request URL
        # at INFO level, which printed the API key into Render's logs.
        url = f"{self.BASE}/{model}:generateContent"
        headers = {"x-goog-api-key": settings.GEMINI_API_KEY or ""}

        full_prompt = (
            f"{system}\n\n{user}\n\n"
            "IMPORTANT: Respond with ONLY valid JSON. No markdown, no code blocks."
        )

        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 4000,
                "topP": 0.95,
                "topK": 40,
                **({"responseMimeType": "application/json"} if json_mode else {}),
            },
        }

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                logger.info(f"gemini.request model={model}")
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                result = resp.json()

            candidates = result.get("candidates", [])
            if candidates and candidates[0].get("content", {}).get("parts"):
                text = candidates[0]["content"]["parts"][0]["text"]
                text = re.sub(r"```json\s*", "", text)
                text = re.sub(r"```\s*", "", text)
                return text.strip()

            raise Exception("No valid response from Gemini")

        except Exception as e:
            logger.error(f"gemini.error error={e}")
            raise