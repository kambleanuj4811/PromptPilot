"""Dashboard numbers come straight from the database. Nothing is hardcoded."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.database_models import (
    Activity, Document, PromptEvaluation, StudySession, VivaSession,
)
from backend.models.schemas import ApiResponse, ok

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _count(db: Session, model, *where) -> int:
    stmt = select(func.count()).select_from(model)
    for condition in where:
        stmt = stmt.where(condition)
    return db.scalar(stmt) or 0


@router.get("/stats", response_model=ApiResponse)
def stats(db: Session = Depends(get_db)):
    return ok({
        "documents": _count(db, Document),
        "documents_ready": _count(db, Document, Document.status == "ready"),
        "study_sessions": _count(db, StudySession),
        "viva_sessions": _count(db, VivaSession),
        "viva_completed": _count(db, VivaSession, VivaSession.status == "completed"),
        "prompt_comparisons": _count(db, PromptEvaluation),
    })


@router.get("/activity", response_model=ApiResponse)
def activity(limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    rows = db.scalars(select(Activity).order_by(Activity.created_at.desc()).limit(limit))
    return ok([{"id": a.id, "type": a.activity_type, "description": a.description,
                "reference_id": a.reference_id, "created_at": a.created_at.isoformat()} for a in rows])