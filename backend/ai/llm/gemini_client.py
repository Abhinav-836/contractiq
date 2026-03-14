import httpx
import json
import re
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
        # Ensure model name doesn't have "models/" prefix
        model = self.model_name
        if model.startswith("models/"):
            model = model.replace("models/", "")
            
        url = f"{self.BASE}/{model}:generateContent?key={settings.GEMINI_API_KEY}"
        
        # Combine system and user for Gemini with explicit JSON instruction
        full_prompt = f"{system}\n\n{user}\n\nIMPORTANT: Respond with ONLY valid JSON. No markdown, no code blocks, no explanations."
        
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 4000,
                "topP": 0.95,
                "topK": 40
            },
        }
        
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                logger.info(f"Calling Gemini API with model: {model}")
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                result = resp.json()
                
                # Extract text from Gemini response
                candidates = result.get("candidates", [])
                if candidates and candidates[0].get("content", {}).get("parts"):
                    text = candidates[0]["content"]["parts"][0]["text"]
                    
                    # Clean up the response - remove markdown code blocks if present
                    text = re.sub(r'```json\s*', '', text)
                    text = re.sub(r'```\s*', '', text)
                    text = text.strip()
                    
                    return text
                else:
                    raise Exception("No valid response from Gemini")
                    
        except Exception as e:
            logger.error(f"Gemini error: {str(e)}")
            raise