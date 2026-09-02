from typing import Optional
from config.settings import settings
from src.llm.openai_compatible_client import OpenAICompatibleClient
from src.llm.lmstudio_client import LMStudioClient
from src.llm.ollama_client import OllamaClient


def get_llm_client(provider: Optional[str] = None):
    prov = provider or settings.LLM_PROVIDER
    base = settings.LLM_BASE_URL
    model = settings.LLM_MODEL
    api_key = settings.LLM_API_KEY

    if prov and prov.lower() == "lmstudio":
        return LMStudioClient(base_url=base, api_key=api_key, model=model)
    if prov and prov.lower() == "ollama":
        return OllamaClient(base_url=base, api_key=api_key, model=model)
    # default
    return OpenAICompatibleClient(base_url=base, api_key=api_key, model=model)
