"""SQLAlchemy tables. Timestamps are stored as UTC. Document text lives in
files and ChromaDB, not here."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


def new_id() -> str:
    return uuid.uuid4().hex


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    original_filename: Mapped[str] = mapped_column(String(255))
    stored_filename: Mapped[str] = mapped_column(String(64))
    file_size_bytes: Mapped[int] = mapped_column(Integer)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="processing")  # processing|ready|failed
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class StudySession(Base):
    __tablename__ = "study_sessions"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    operation: Mapped[str] = mapped_column(String(30))
    topic: Mapped[str] = mapped_column(String(300))
    academic_level: Mapped[str] = mapped_column(String(30))
    answer_length: Mapped[str] = mapped_column(String(20))
    output_style: Mapped[str] = mapped_column(String(30))
    document_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class VivaSession(Base):
    __tablename__ = "viva_sessions"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    topic: Mapped[str] = mapped_column(String(300))
    difficulty: Mapped[str] = mapped_column(String(20))
    document_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    questions_json: Mapped[str] = mapped_column(Text)
    current_index: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="in_progress")
    summary_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    answers: Mapped[list["VivaAnswer"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class VivaAnswer(Base):
    __tablename__ = "viva_answers"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("viva_sessions.id"))
    question_index: Mapped[int] = mapped_column(Integer)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    evaluation_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    session: Mapped[VivaSession] = relationship(back_populates="answers")


class PromptEvaluation(Base):
    __tablename__ = "prompt_evaluations"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    prompt_a: Mapped[str] = mapped_column(Text)
    prompt_b: Mapped[str] = mapped_column(Text)
    summary_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    results: Mapped[list["EvaluationResult"]] = relationship(
        back_populates="evaluation", cascade="all, delete-orphan"
    )


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    evaluation_id: Mapped[str] = mapped_column(ForeignKey("prompt_evaluations.id"))
    test_input: Mapped[str] = mapped_column(Text)
    variant: Mapped[str] = mapped_column(String(1))  # "A" or "B"
    output: Mapped[str] = mapped_column(Text)
    scores_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    deterministic_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    evaluation: Mapped[PromptEvaluation] = relationship(back_populates="results")


class Activity(Base):
    __tablename__ = "activities"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    activity_type: Mapped[str] = mapped_column(String(30))
    description: Mapped[str] = mapped_column(String(300))
    reference_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)