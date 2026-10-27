from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies import get_ai_provider, get_embedder, get_retrieval
from backend.models.research_schemas import ResearchRequest
from backend.models.schemas import ApiResponse, ok
from backend.services.research_service import ResearchService

router = APIRouter(prefix="/api/research", tags=["research"])


def get_research_service(db: Session = Depends(get_db), provider=Depends(get_ai_provider),
                         embedder=Depends(get_embedder), retrieval=Depends(get_retrieval)):
    return ResearchService(db, provider, embedder, retrieval)


@router.post("/summarize", response_model=ApiResponse)
def summarize(req: ResearchRequest, s: ResearchService = Depends(get_research_service)):
    return ok(s.summarize(req.document_id))


@router.post("/analyze", response_model=ApiResponse)
def analyze(req: ResearchRequest, s: ResearchService = Depends(get_research_service)):
    return ok(s.analyze(req.document_id))