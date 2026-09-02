from typing import Any, Dict, Optional
from src.llm.openai_compatible_client import OpenAICompatibleClient
from src.utils.logger import get_logger

logger = get_logger("ollama_client")


class OllamaClient(OpenAICompatibleClient):
    """Client for Ollama; Ollama provides an OpenAI-like HTTP API at a local port."""

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, model: Optional[str] = None):
        super().__init__(base_url=base_url, api_key=api_key, model=model)

    def health_check(self) -> bool:
        try:
            base = self.base_url.rstrip("/")
            import httpx

            resp = httpx.get(base, timeout=5)
            return resp.status_code == 200
        except Exception:
            logger.exception("Ollama health check failed")
            return False

    def get_model_info(self) -> Dict[str, Any]:
        return {"provider": "ollama", "model": self.model}
