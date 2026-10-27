from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class CompareRequest(BaseModel):
    prompt_a: str = Field(min_length=3, max_length=4000)
    prompt_b: str = Field(min_length=3, max_length=4000)
    test_questions: list[str] = Field(min_length=1, max_length=3)
    expected_format: Literal["text", "json"] = "text"
    required_fields: list[str] = Field(default_factory=list, max_length=10)
    max_words: int | None = Field(default=None, ge=1, le=5000)

    @field_validator("prompt_a", "prompt_b")
    @classmethod
    def prompt_not_blank(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("prompts must contain at least 3 characters")
        return v

    @field_validator("test_questions")
    @classmethod
    def clean_questions(cls, v: list[str]) -> list[str]:
        cleaned = [q.strip() for q in v]
        if any(not q or len(q) > 1000 for q in cleaned):
            raise ValueError("every test question must be 1-1000 characters")
        return cleaned

    @model_validator(mode="after")
    def fields_need_json(self):
        if self.required_fields and self.expected_format != "json":
            raise ValueError("required_fields only applies when expected_format is json")
        return self


class CriterionScore(BaseModel):
    score: float = Field(ge=0, le=10)
    justification: str
    issues: list[str] = Field(default_factory=list)


class JudgeOutput(BaseModel):
    accuracy: CriterionScore
    completeness: CriterionScore
    relevance: CriterionScore
    consistency: CriterionScore
    formatting: CriterionScore