from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    document_id: str = Field(min_length=1)


class PaperFinding(BaseModel):
    statement: str
    quote: str
    source: int


class ResearchAspect(BaseModel):
    found_in_document: bool
    findings: list[PaperFinding] = Field(default_factory=list)
    interpretation: str = ""


class ResearchAnalysisOutput(BaseModel):
    overview: str
    objectives: ResearchAspect
    methodology: ResearchAspect
    key_findings: ResearchAspect
    limitations: ResearchAspect
    conclusions: ResearchAspect


class ResearchSummaryOutput(BaseModel):
    summary: str
    key_points: list[str] = Field(min_length=1)