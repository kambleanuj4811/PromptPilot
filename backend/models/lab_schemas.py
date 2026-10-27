from typing import Literal

from pydantic import BaseModel, Field


class LabRunRequest(BaseModel):
    technique_id: Literal[
        "zero_shot", "few_shot", "role", "chaining", "structured", "context_aware", "validation"
    ]
    user_input: str = Field(default="", max_length=500)


class TopicCard(BaseModel):
    title: str
    definition: str
    key_points: list[str] = Field(min_length=2, max_length=5)
    difficulty: Literal["beginner", "intermediate", "advanced"]