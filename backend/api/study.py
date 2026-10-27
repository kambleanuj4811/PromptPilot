from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies import get_ai_provider, get_embedder, get_retrieval
from backend.models.requests import StudyRequest
from backend.models.schemas import ApiResponse, ok
from backend.services.study_service import StudyService

router = APIRouter(prefix="/api/study", tags=["study"])


def get_study_service(db: Session = Depends(get_db), provider=Depends(get_ai_provider),
                      embedder=Depends(get_embedder), retrieval=Depends(get_retrieval)):
    return StudyService(db, provider, embedder, retrieval)


@router.post("/explain", response_model=ApiResponse)
def explain(req: StudyRequest, s: StudyService = Depends(get_study_service)):
    return ok(s.run("explain", req))


@router.post("/summarize", response_model=ApiResponse)
def summarize(req: StudyRequest, s: StudyService = Depends(get_study_service)):
    return ok(s.run("summarize", req))


@router.post("/revision-notes", response_model=ApiResponse)
def revision_notes(req: StudyRequest, s: StudyService = Depends(get_study_service)):
    return ok(s.run("revision_notes", req))


@router.post("/mcqs", response_model=ApiResponse)
def mcqs(req: StudyRequest, s: StudyService = Depends(get_study_service)):
    return ok(s.run("mcqs", req))


@router.post("/questions", response_model=ApiResponse)
def questions(req: StudyRequest, s: StudyService = Depends(get_study_service)):
    return ok(s.run("questions", req))


@router.post("/exam-answers", response_model=ApiResponse)
def exam_answers(req: StudyRequest, s: StudyService = Depends(get_study_service)):
    return ok(s.run("exam_answer", req))