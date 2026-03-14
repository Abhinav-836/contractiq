# ai/llm/ollama_client.py
import httpx
import json
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
        return settings.OLLAMA_MODEL  # gpt-os-20b

    async def complete(self, system: str, user: str, json_mode: bool = True) -> str:
        """
        Complete using Ollama with GPT-OS 20B
        Fixed endpoint handling for Ollama cloud API
        """
        # Prepare headers for cloud authentication
        headers = {
            "Content-Type": "application/json"
        }
        
        if settings.OLLAMA_API_KEY:
            headers["Authorization"] = f"Bearer {settings.OLLAMA_API_KEY}"
            logger.info("Using Ollama API key authentication")
        
        try:
            if settings.OLLAMA_IS_CLOUD:
                # FIXED: Ollama cloud uses /api/chat endpoint, not /v1/chat/completions
                base_url = settings.OLLAMA_BASE_URL.rstrip('/')
                url = f"{base_url}/api/chat"
                
                payload = {
                    "model": settings.OLLAMA_MODEL,  # gpt-os-20b
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user}
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.2,
                        "num_predict": 4000
                    }
                }
                
                # Add format for JSON mode if supported
                if json_mode:
                    payload["format"] = "json"
                
                logger.info(f"Calling Ollama cloud API at {url} with model {settings.OLLAMA_MODEL}")
                
                async with httpx.AsyncClient(timeout=180) as client:
                    resp = await client.post(url, json=payload, headers=headers)
                    
                    if resp.status_code == 401:
                        logger.error("Ollama authentication failed - check your API key")
                        raise Exception("Ollama authentication failed: Invalid API key")
                    
                    if resp.status_code == 404:
                        logger.error(f"Model {settings.OLLAMA_MODEL} not found")
                        logger.error("Available models: https://ollama.com/models")
                        raise Exception(f"Ollama model {settings.OLLAMA_MODEL} not found")
                    
                    resp.raise_for_status()
                    data = resp.json()
                    
                    # Extract content from Ollama response format
                    if "message" in data and "content" in data["message"]:
                        return data["message"]["content"]
                    elif "response" in data:
                        return data["response"]
                    else:
                        logger.error(f"Unexpected Ollama response format: {data}")
                        raise Exception("Unexpected Ollama response format")
            else:
                # Local Ollama endpoint
                url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate"
                
                payload = {
                    "model": settings.OLLAMA_MODEL,
                    "prompt": f"{system}\n\n{user}",
                    "stream": False,
                    "options": {
                        "temperature": 0.2,
                        "num_predict": 4000
                    }
                }
                if json_mode:
                    payload["format"] = "json"
                
                logger.info(f"Calling local Ollama at {url}")
                
                async with httpx.AsyncClient(timeout=180) as client:
                    resp = await client.post(url, json=payload, headers=headers)
                    resp.raise_for_status()
                    response_data = resp.json()
                    return response_data.get("response", "")
                    
        except httpx.TimeoutException:
            logger.error("Ollama timeout - check your connection")
            raise Exception("Ollama request timed out")
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama HTTP error: {e.response.status_code}")
            if e.response.status_code == 301:
                logger.error("Got 301 redirect - check your OLLAMA_BASE_URL setting")
                logger.error(f"Current URL: {settings.OLLAMA_BASE_URL}")
                logger.error("For cloud: Use https://api.ollama.com (no /v1)")
            elif e.response.status_code == 401:
                logger.error("Authentication failed - check your OLLAMA_API_KEY")
            elif e.response.status_code == 404:
                logger.error(f"Model {settings.OLLAMA_MODEL} not found")
                logger.error("Check if the model name is correct at https://ollama.com/models")
            raise Exception(f"Ollama HTTP error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Ollama error: {str(e)}")
            raise