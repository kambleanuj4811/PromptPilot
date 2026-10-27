from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies import get_ai_provider, get_embedder, get_retrieval
from backend.models.requests import AskRequest
from backend.models.schemas import ApiResponse, ok
from backend.services.qa_service import QAService

router = APIRouter(prefix="/api/chat", tags=["document-qa"])


def get_qa_service(db: Session = Depends(get_db), provider=Depends(get_ai_provider),
                   embedder=Depends(get_embedder), retrieval=Depends(get_retrieval)):
    return QAService(db, provider, embedder, retrieval)


@router.post("/ask", response_model=ApiResponse)
def ask(req: AskRequest, service: QAService = Depends(get_qa_service)):
    return ok(service.ask(req.question.strip(), req.document_ids))