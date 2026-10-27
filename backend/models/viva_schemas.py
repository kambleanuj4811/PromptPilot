from typing import Literal

from pydantic import BaseModel, Field


class VivaStartRequest(BaseModel):
    topic: str = Field(default="", max_length=300)
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    count: int = Field(default=5, ge=1, le=10)
    document_id: str | None = None


class VivaEvaluateRequest(BaseModel):
    session_id: str = Field(min_length=1)
    answer: str = Field(max_length=4000)


class VivaNextRequest(BaseModel):
    session_id: str = Field(min_length=1)


class VivaQuestion(BaseModel):
    question: str
    expected_points: list[str] = Field(min_length=1)


class VivaQuestionsOutput(BaseModel):
    questions: list[VivaQuestion] = Field(min_length=1)


class VivaEvaluation(BaseModel):
    correctness: int = Field(ge=0, le=10)
    conceptual_understanding: int = Field(ge=0, le=10)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    feedback: str
    improved_answer: str


class VivaSummaryOutput(BaseModel):
    overall_assessment: str
    strengths: list[str] = Field(default_factory=list)
    areas_for_improvement: list[str] = Field(default_factory=list)
    study_suggestions: list[str] = Field(default_factory=list)