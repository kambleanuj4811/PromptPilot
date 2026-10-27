"""Local embeddings via sentence-transformers (loaded lazily on first use)."""
from backend.errors import AppError


class EmbeddingService:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = None

    def _load(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self.model_name)
            except Exception as exc:
                raise AppError(
                    f"Could not load embedding model '{self.model_name}' ({type(exc).__name__}). "
                    "The first run needs internet to download it. Fallback: download a model "
                    "folder once and set EMBEDDING_MODEL in .env to that folder's path.",
                    503,
                ) from None
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = self._load().encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return vectors.tolist()