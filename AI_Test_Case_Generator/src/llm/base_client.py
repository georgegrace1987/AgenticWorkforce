from typing import Any, Dict, Optional
from abc import ABC, abstractmethod


class BaseLLMClient(ABC):
    """Abstract base LLM client defining required methods for the application."""

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate free text from the LLM."""
        raise NotImplementedError()

    @abstractmethod
    def generate_structured(self, prompt: str, schema: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Generate structured JSON output validated against `schema`."""
        raise NotImplementedError()

    @abstractmethod
    def health_check(self) -> bool:
        """Check whether the LLM endpoint is reachable and healthy."""
        raise NotImplementedError()

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Return model metadata such as name and context size."""
        raise NotImplementedError()
