"""FastAPI dependencies. Tests override get_ai_provider with a fake."""
from functools import lru_cache

from backend.config import get_settings
from backend.services.ai_provider import AIProvider
from backend.services.gemini_provider import GeminiProvider


@lru_cache
def get_ai_provider() -> AIProvider:
    settings = get_settings()
    return GeminiProvider(api_key=settings.gemini_api_key, model=settings.gemini_model)