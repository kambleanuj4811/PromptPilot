"""GET /api/health. Add ?check_ai=true to make one tiny real Gemini call."""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.config import Settings, get_settings
from backend.database import get_db
from backend.dependencies import get_ai_provider
from backend.models.schemas import ApiResponse, ok
from backend.services.ai_provider import AIProvider, AIProviderError

router = APIRouter(prefix="/api", tags=["health"])
VERSION = "0.1.0"


@router.get("/health", response_model=ApiResponse)
def health(
    check_ai: bool = False,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    provider: AIProvider = Depends(get_ai_provider),
):
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    ai = {
        "provider": provider.name,
        "model": provider.model,
        "api_key_configured": provider.is_configured(),
        "check": None,
    }
    if check_ai:
        try:
            reply = provider.generate_text("Reply with exactly the word: OK")
            ai["check"] = {"ok": True, "reply": reply.strip()[:50]}
        except AIProviderError as exc:
            ai["check"] = {"ok": False, "error": exc.message}

    return ok(
        {
            "status": "ok" if db_ok else "degraded",
            "version": VERSION,
            "database_ok": db_ok,
            "ai": ai,
            "embedding_model": settings.embedding_model,
        }
    )