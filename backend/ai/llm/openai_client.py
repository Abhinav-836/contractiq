from ai.llm.base import BaseLLMClient
from core.config import settings
from core.logger import get_logger
import openai
from openai import AsyncOpenAI

logger = get_logger(__name__)


class OpenAIClient(BaseLLMClient):
    def __init__(self):
        self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return settings.OPENAI_MODEL

    async def complete(self, system: str, user: str, json_mode: bool = True) -> str:
        try:
            kwargs = {
                "model": settings.OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.2,
                "max_tokens": 4000,
            }
            
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            
            logger.info("Calling OpenAI API")
            response = await self._client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI error: {str(e)}")
            raise