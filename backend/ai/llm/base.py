from abc import ABC, abstractmethod
from typing import Optional


class BaseLLMClient(ABC):
    @abstractmethod
    async def complete(self, system: str, user: str, json_mode: bool = True) -> str:
        """Send a chat completion request and return the response text."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        ...
