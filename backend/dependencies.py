"""FastAPI dependencies. Tests override these with fakes."""
from functools import lru_cache

import chromadb

from backend.config import get_settings
from backend.services.ai_provider import AIProvider
from backend.services.embedding_service import EmbeddingService
from backend.services.gemini_provider import GeminiProvider
from backend.services.retrieval_service import RetrievalService


@lru_cache
def get_ai_provider() -> AIProvider:
    settings = get_settings()
    return GeminiProvider(api_key=settings.gemini_api_key, model=settings.gemini_model)


@lru_cache
def get_embedder() -> EmbeddingService:
    return EmbeddingService(get_settings().embedding_model)


@lru_cache
def get_retrieval() -> RetrievalService:
    path = get_settings().chroma_persist_directory
    path.mkdir(parents=True, exist_ok=True)
    return RetrievalService(chromadb.PersistentClient(path=str(path)))