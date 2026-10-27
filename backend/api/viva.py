from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies import get_ai_provider, get_embedder, get_retrieval
from backend.models.schemas import ApiResponse, ok
from backend.models.viva_schemas import VivaEvaluateRequest, VivaNextRequest, VivaStartRequest
from backend.services.viva_service import VivaService

router = APIRouter(prefix="/api/viva", tags=["viva"])


def get_viva_service(db: Session = Depends(get_db), provider=Depends(get_ai_provider),
                     embedder=Depends(get_embedder), retrieval=Depends(get_retrieval)):
    return VivaService(db, provider, embedder, retrieval)


@router.post("/start", response_model=ApiResponse, status_code=201)
def start(req: VivaStartRequest, s: VivaService = Depends(get_viva_service)):
    return ok(s.start(req))


@router.post("/evaluate", response_model=ApiResponse)
def evaluate(req: VivaEvaluateRequest, s: VivaService = Depends(get_viva_service)):
    return ok(s.evaluate(req.session_id, req.answer))


@router.post("/next", response_model=ApiResponse)
def next_question(req: VivaNextRequest, s: VivaService = Depends(get_viva_service)):
    return ok(s.next(req.session_id))


@router.get("/{session_id}", response_model=ApiResponse)
def get_session(session_id: str, s: VivaService = Depends(get_viva_service)):
    return ok(s.detail(session_id))