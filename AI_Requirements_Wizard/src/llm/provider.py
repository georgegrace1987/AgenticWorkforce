import json
import logging
from pathlib import Path
from typing import Any

import httpx

from config.settings import settings

logger = logging.getLogger("wizard.llm")
PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "clarification.txt"


class ClarificationProvider:
    """Use a local OpenAI-compatible model as a requirements analyst."""

    def _request(self, prompt: str) -> dict[str, Any]:
        url = f"{settings.LLM_BASE_URL.rstrip('/')}/chat/completions"
        payload = {
            "model": settings.LLM_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": settings.LLM_TEMPERATURE,
            "max_tokens": settings.LLM_MAX_TOKENS,
        }
        headers = {"Content-Type": "application/json"}
        if settings.LLM_API_KEY:
            headers["Authorization"] = f"Bearer {settings.LLM_API_KEY}"
        response = httpx.post(
            url,
            json=payload,
            headers=headers,
            timeout=min(settings.REQUEST_TIMEOUT_SECONDS, 15),
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        if "```" in content:
            content = content.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            raise ValueError("LLM response must be a JSON object")
        return parsed

    def analyze(self, state: dict[str, Any], message: str) -> dict[str, Any]:
        prompt_template = PROMPT_PATH.read_text(encoding="utf-8")
        prompt = prompt_template.format(
            requirements=json.dumps(state, ensure_ascii=True),
            latest_message=message,
        )
        try:
            result = self._request(prompt)
            if not isinstance(result.get("questions", []), list):
                raise ValueError("LLM questions field is not a list")
            if not isinstance(result.get("requirements", {}), dict):
                raise ValueError("LLM requirements field is not an object")
            return result
        except (httpx.HTTPError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            logger.warning("Local LLM unavailable: %s", error)
            return {}

    def generate_questions(self, state: dict[str, Any], message: str) -> list[str]:
        return [str(question).strip() for question in self.analyze(state, message).get("questions", []) if str(question).strip()][:3]
