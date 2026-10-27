from typing import Literal

from pydantic import BaseModel, Field


class StudyRequest(BaseModel):
    topic: str = Field(default="", max_length=300)
    text: str = Field(default="", max_length=20000)  # pasted notes (summarize only)
    academic_level: Literal["school", "undergraduate", "postgraduate", "professional"] = "undergraduate"
    length: Literal["short", "medium", "detailed"] = "medium"
    style: Literal["simple", "exam", "technical"] = "simple"
    count: int = Field(default=5, ge=1, le=10)
    document_id: str | None = None


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    document_ids: list[str] | None = None  # None or empty = all ready documents