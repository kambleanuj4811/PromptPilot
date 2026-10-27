"""Pydantic schemas for structured AI output. Invalid output triggers the
repair/retry loop in AIProvider.generate_structured."""
from pydantic import BaseModel, Field, model_validator


class EvidenceItem(BaseModel):
    source: int
    quote: str


class QAModelOutput(BaseModel):
    sufficient_evidence: bool
    answer: str
    evidence: list[EvidenceItem] = Field(default_factory=list)
    explanation: str = ""


class ExplainOutput(BaseModel):
    title: str
    overview: str
    key_points: list[str] = Field(min_length=1)
    example: str
    common_mistakes: list[str] = Field(default_factory=list)
    summary: str


class SummaryOutput(BaseModel):
    title: str
    summary: str
    key_points: list[str] = Field(min_length=1)


class RevisionSection(BaseModel):
    heading: str
    points: list[str] = Field(min_length=1)


class KeyTerm(BaseModel):
    term: str
    definition: str


class RevisionOutput(BaseModel):
    title: str
    sections: list[RevisionSection] = Field(min_length=1)
    key_terms: list[KeyTerm] = Field(default_factory=list)


class MCQ(BaseModel):
    question: str
    options: list[str]
    correct_index: int
    explanation: str

    @model_validator(mode="after")
    def check_structure(self):
        if len(self.options) != 4:
            raise ValueError("each MCQ needs exactly 4 options")
        if len({o.strip().lower() for o in self.options}) != 4:
            raise ValueError("MCQ options must be distinct")
        if not 0 <= self.correct_index <= 3:
            raise ValueError("correct_index must be between 0 and 3")
        return self


class MCQOutput(BaseModel):
    questions: list[MCQ] = Field(min_length=1)


class ShortQuestion(BaseModel):
    question: str
    model_answer: str
    marks: int = Field(default=2, ge=1, le=10)


class ShortQuestionsOutput(BaseModel):
    questions: list[ShortQuestion] = Field(min_length=1)


class ExamSection(BaseModel):
    heading: str
    content: str


class ExamAnswerOutput(BaseModel):
    question: str
    introduction: str
    sections: list[ExamSection] = Field(min_length=1)
    conclusion: str
    keywords: list[str] = Field(default_factory=list)