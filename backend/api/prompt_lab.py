from fastapi import APIRouter, Depends

from backend.dependencies import get_ai_provider
from backend.models.lab_schemas import LabRunRequest
from backend.models.schemas import ApiResponse, ok
from backend.services.prompt_lab_service import list_techniques, run_technique

router = APIRouter(prefix="/api/prompt-lab", tags=["prompt-lab"])


@router.get("/techniques", response_model=ApiResponse)
def techniques():
    return ok(list_techniques())


@router.post("/run", response_model=ApiResponse)
def run(req: LabRunRequest, provider=Depends(get_ai_provider)):
    return ok(run_technique(provider, req.technique_id, req.user_input))