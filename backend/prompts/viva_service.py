"""Viva workflow: generate questions -> evaluate answers -> next -> summary."""
import json

from sqlalchemy.orm import Session

from backend.errors import AppError
from backend.models.database_models import Activity, VivaAnswer, VivaSession, utcnow
from backend.models.viva_schemas import (
    VivaEvaluation, VivaQuestionsOutput, VivaStartRequest, VivaSummaryOutput,
)
from backend.prompts.viva_prompts import (
    build_evaluation_prompt, build_questions_prompt, build_summary_prompt,
)
from backend.services.context_service import format_chunks, get_ready_document

MIN_SCORE = 0.15
CONTEXT_TOP_K = 4
DISCLAIMER = "AI-generated grading is an estimate, not an authoritative academic assessment."


class VivaService:
    def __init__(self, db: Session, provider, embedder, retrieval):
        self.db, self.provider, self.embedder, self.retrieval = db, provider, embedder, retrieval

    def _get(self, session_id: str) -> VivaSession:
        session = self.db.get(VivaSession, session_id)
        if not session:
            raise AppError("Viva session not found.", 404)
        return session

    def _context(self, document_id, query, strict):
        if not document_id:
            return None
        try:
            doc = get_ready_document(self.db, document_id)
        except AppError:
            if strict:
                raise
            return None  # document deleted mid-session: grade without it
        qvec = self.embedder.embed([query])[0]
        chunks = [c for c in self.retrieval.search(qvec, [doc.id], CONTEXT_TOP_K) if c.score >= MIN_SCORE]
        if not chunks and strict:
            raise AppError("The selected document has no content related to this topic.", 422)
        return format_chunks(chunks) if chunks else None

    @staticmethod
    def _public_question(questions, idx):
        return {"index": idx, "number": idx + 1, "total": len(questions),
                "question": questions[idx]["question"]}  # expected_points stay server-side

    def start(self, req: VivaStartRequest) -> dict:
        topic = req.topic.strip()
        if not topic:
            raise AppError("Please enter a subject or topic.", 422)
        context = self._context(req.document_id, topic, strict=True)
        built = build_questions_prompt(topic, req.difficulty, req.count, context)
        out = self.provider.generate_structured(built.user, VivaQuestionsOutput, system=built.system)
        questions = [q.model_dump() for q in out.questions[: req.count]]
        notes = []
        if len(questions) < req.count:
            notes.append(f"The AI produced {len(questions)} of the {req.count} requested questions.")
        session = VivaSession(topic=topic, difficulty=req.difficulty, document_id=req.document_id,
                              questions_json=json.dumps(questions))
        self.db.add(session)
        self.db.flush()
        self.db.add(Activity(activity_type="viva", reference_id=session.id,
                             description=f"Started viva: {topic[:60]}"))
        self.db.commit()
        return {"session_id": session.id, "topic": topic, "difficulty": req.difficulty,
                "total": len(questions), "question": self._public_question(questions, 0),
                "notes": notes, "disclaimer": DISCLAIMER}

    def evaluate(self, session_id: str, answer_text: str) -> dict:
        session = self._get(session_id)
        if session.status == "completed":
            raise AppError("This viva session is already complete.", 409)
        answer_text = answer_text.strip()
        if not answer_text:
            raise AppError("Please write an answer before submitting.", 422)
        idx = session.current_index
        if any(a.question_index == idx for a in session.answers):
            raise AppError("This question was already answered. Continue to the next question.", 409)
        questions = json.loads(session.questions_json)
        q = questions[idx]
        context = self._context(session.document_id, q["question"], strict=False)
        built = build_evaluation_prompt(session.topic, session.difficulty, q["question"],
                                        q["expected_points"], answer_text, context)
        ev = self.provider.generate_structured(built.user, VivaEvaluation, system=built.system)
        self.db.add(VivaAnswer(session_id=session.id, question_index=idx, question=q["question"],
                               answer=answer_text, score=float(ev.correctness),
                               evaluation_json=ev.model_dump_json()))
        self.db.commit()
        return {"question_index": idx, "evaluation": ev.model_dump(),
                "is_last": idx + 1 >= len(questions), "disclaimer": DISCLAIMER}

    def next(self, session_id: str) -> dict:
        session = self._get(session_id)
        if session.status == "completed":
            return {"completed": True, "summary": json.loads(session.summary_json)}
        idx = session.current_index
        if not any(a.question_index == idx for a in session.answers):
            raise AppError("Answer the current question before continuing.", 409)
        questions = json.loads(session.questions_json)
        if idx + 1 < len(questions):
            session.current_index = idx + 1
            self.db.commit()
            return {"completed": False, "question": self._public_question(questions, idx + 1)}
        return {"completed": True, "summary": self._finish(session)}

    def _finish(self, session: VivaSession) -> dict:
        answers = sorted(session.answers, key=lambda a: a.question_index)
        evals = [json.loads(a.evaluation_json) for a in answers]
        avg_c = round(sum(e["correctness"] for e in evals) / len(evals), 1)
        avg_u = round(sum(e["conceptual_understanding"] for e in evals) / len(evals), 1)
        built = build_summary_prompt(session.topic, session.difficulty,
                                     [(a.question, e) for a, e in zip(answers, evals)])
        narrative = self.provider.generate_structured(built.user, VivaSummaryOutput, system=built.system)
        summary = {
            "questions_answered": len(answers),
            "total_questions": len(json.loads(session.questions_json)),
            "average_correctness": avg_c,         # calculated in code, not by the model
            "average_conceptual_understanding": avg_u,
            **narrative.model_dump(),
            "disclaimer": DISCLAIMER,
        }
        session.status = "completed"
        session.completed_at = utcnow()
        session.summary_json = json.dumps(summary)
        self.db.add(Activity(activity_type="viva", reference_id=session.id,
                             description=f"Completed viva: {session.topic[:60]}"))
        self.db.commit()
        return summary

    def detail(self, session_id: str) -> dict:
        session = self._get(session_id)
        questions = json.loads(session.questions_json)
        shown = questions if session.status == "completed" else questions[: session.current_index + 1]
        answers = sorted(session.answers, key=lambda a: a.question_index)
        return {
            "session_id": session.id, "topic": session.topic, "difficulty": session.difficulty,
            "status": session.status, "total": len(questions), "current_index": session.current_index,
            "questions": [q["question"] for q in shown],
            "answers": [{"question_index": a.question_index, "question": a.question,
                         "answer": a.answer, "score": a.score,
                         "evaluation": json.loads(a.evaluation_json)} for a in answers],
            "summary": json.loads(session.summary_json) if session.summary_json else None,
            "disclaimer": DISCLAIMER,
        }