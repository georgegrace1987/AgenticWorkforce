from typing import Any, Dict, Optional
import httpx
from src.llm.base_client import BaseLLMClient
from src.utils.logger import get_logger
from config.settings import settings

logger = get_logger("openai_compatible_client")


class OpenAICompatibleClient(BaseLLMClient):
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, model: Optional[str] = None):
        self.base_url = base_url or settings.LLM_BASE_URL
        self.api_key = api_key or settings.LLM_API_KEY
        self.model = model or settings.LLM_MODEL
        self.timeout = settings.REQUEST_TIMEOUT_SECONDS

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def generate(self, prompt: str, temperature: float = None, max_tokens: int = None, **kwargs) -> Dict[str, Any]:
        """Send a chat/completion style request to an OpenAI-compatible endpoint."""
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature if temperature is not None else settings.LLM_TEMPERATURE,
            "max_tokens": max_tokens if max_tokens is not None else settings.LLM_MAX_TOKENS,
        }
        try:
            resp = httpx.post(url, json=payload, headers=self._headers(), timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.exception("LLM generate request failed: %s", e)
            return {"error": str(e)}

    def generate_structured(self, prompt: str, schema: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        # Use the same endpoint but constrain the prompt to request JSON
        structured_prompt = prompt + "\n\nRespond with valid JSON only following the schema. If a field is missing, use 'Not specified'."
        resp = self.generate(structured_prompt, **kwargs)
        return resp

    def health_check(self) -> bool:
        try:
            url = f"{self.base_url.rstrip('/')}/"
            resp = httpx.get(url, timeout=5)
            return resp.status_code in (200, 204)
        except Exception:
            logger.exception("LLM health check failed")
            return False

    def get_model_info(self) -> Dict[str, Any]:
        return {"provider": settings.LLM_PROVIDER, "model": self.model}
