from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies import get_ai_provider
from backend.models.eval_schemas import CompareRequest
from backend.models.schemas import ApiResponse, ok
from backend.services.evaluation_service import EvaluationService

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])


def get_evaluation_service(db: Session = Depends(get_db), provider=Depends(get_ai_provider)):
    return EvaluationService(db, provider)


@router.post("/compare", response_model=ApiResponse, status_code=201)
def compare(req: CompareRequest, s: EvaluationService = Depends(get_evaluation_service)):
    return ok(s.compare(req))


@router.get("/history", response_model=ApiResponse)  # must stay above /{evaluation_id}
def history(s: EvaluationService = Depends(get_evaluation_service)):
    return ok(s.history())


@router.get("/{evaluation_id}", response_model=ApiResponse)
def get_evaluation(evaluation_id: str, s: EvaluationService = Depends(get_evaluation_service)):
    return ok(s.get(evaluation_id))