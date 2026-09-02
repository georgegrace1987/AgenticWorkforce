from typing import Any, Dict, Optional
from src.llm.openai_compatible_client import OpenAICompatibleClient
from src.utils.logger import get_logger
from config import settings

logger = get_logger("lmstudio_client")


class LMStudioClient(OpenAICompatibleClient):
    """Client for LM Studio using OpenAI-compatible endpoints where possible."""

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, model: Optional[str] = None):
        super().__init__(base_url=base_url, api_key=api_key, model=model)

    def health_check(self) -> bool:
        # LM Studio often exposes /health or root; try both
        try:
            base = self.base_url.rstrip("/")
            for path in ("/health", "/v1", "/"):
                try:
                    import httpx

                    resp = httpx.get(f"{base}{path}", timeout=5)
                    if resp.status_code == 200:
                        return True
                except Exception:
                    continue
            return False
        except Exception:
            logger.exception("LMStudio health check failed")
            return False

    def get_model_info(self) -> Dict[str, Any]:
        return {"provider": "lmstudio", "model": self.model}
