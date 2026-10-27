"""Central configuration, read once from environment variables / .env."""
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


class ConfigError(Exception):
    """Raised when configuration is invalid."""


def _resolve_path(raw: str) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else (ROOT_DIR / path).resolve()


def _resolve_db_url(raw: str) -> str:
    """Make relative sqlite paths relative to the project root, not the CWD."""
    prefix = "sqlite:///"
    if not raw.startswith(prefix) or raw == "sqlite://" or ":memory:" in raw:
        return raw
    path = Path(raw[len(prefix):])
    if not path.is_absolute():
        path = (ROOT_DIR / path).resolve()
    return f"{prefix}{path.as_posix()}"


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    gemini_model: str
    database_url: str
    chroma_persist_directory: Path
    upload_directory: Path
    max_upload_size_mb: int
    embedding_model: str
    frontend_origin: str

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def ai_configured(self) -> bool:
        return bool(self.gemini_api_key)


@lru_cache
def get_settings() -> Settings:
    try:
        max_mb = int(os.getenv("MAX_UPLOAD_SIZE_MB", "20"))
    except ValueError as exc:
        raise ConfigError("MAX_UPLOAD_SIZE_MB must be a whole number.") from exc
    if max_mb <= 0:
        raise ConfigError("MAX_UPLOAD_SIZE_MB must be greater than 0.")

    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite").strip(),
        database_url=_resolve_db_url(
            os.getenv("DATABASE_URL", "sqlite:///./backend/data/promptpilot.db")
        ),
        chroma_persist_directory=_resolve_path(
            os.getenv("CHROMA_PERSIST_DIRECTORY", "./backend/data/chroma")
        ),
        upload_directory=_resolve_path(os.getenv("UPLOAD_DIRECTORY", "./backend/uploads")),
        max_upload_size_mb=max_mb,
        embedding_model=os.getenv(
            "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        ).strip(),
        frontend_origin=os.getenv("FRONTEND_ORIGIN", "http://localhost:5173").strip(),
    )