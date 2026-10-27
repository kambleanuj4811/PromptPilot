import json

from sqlalchemy.orm import Session

from backend.errors import AppError
from backend.models.database_models import Activity, StudySession
from backend.models.requests import StudyRequest
from backend.prompts.study_prompts import build_study_prompt
from backend.services.context_service import chunk_to_source, format_chunks, get_ready_document

MIN_SCORE = 0.15
CONTEXT_TOP_K = 6


class StudyService:
    def __init__(self, db: Session, provider, embedder, retrieval):
        self.db, self.provider, self.embedder, self.retrieval = db, provider, embedder, retrieval

    def run(self, operation: str, req: StudyRequest) -> dict:
        topic, text = req.topic.strip(), req.text.strip()
        if operation == "summarize":
            if not text and not req.document_id:
                raise AppError("Provide notes text or select a document to summarize.", 422)
        elif not topic:
            raise AppError("Please enter a topic.", 422)

        notes: list[str] = []
        context, sources = None, []
        if operation == "summarize" and text:
            context = text
        elif req.document_id:
            doc = get_ready_document(self.db, req.document_id)
            if operation == "summarize":
                chunks = self.retrieval.get_document_chunks(doc.id)
                total = self.retrieval.count_for_document(doc.id)
                if len(chunks) < total:
                    notes.append(f"Only the first {len(chunks)} of {total} sections were used (length limit).")
            else:
                qvec = self.embedder.embed([topic])[0]
                chunks = [c for c in self.retrieval.search(qvec, [doc.id], CONTEXT_TOP_K)
                          if c.score >= MIN_SCORE]
                if not chunks:
                    raise AppError("The selected document has no content related to this topic.", 422)
            if not chunks:
                raise AppError("The selected document has no readable content.", 422)
            context = format_chunks(chunks)
            sources = [chunk_to_source(i, c) for i, c in enumerate(chunks, 1)]

        built, schema = build_study_prompt(
            operation, topic=topic, level=req.academic_level, length=req.length,
            style=req.style, count=req.count, context=context,
        )
        result = self.provider.generate_structured(built.user, schema, system=built.system).model_dump()

        if operation in ("mcqs", "questions"):
            items = result["questions"]
            if len(items) > req.count:
                result["questions"] = items[: req.count]
            elif len(items) < req.count:
                notes.append(f"The AI produced {len(items)} of the {req.count} requested questions.")

        label = topic[:60] or "document summary"
        session = StudySession(
            operation=operation, topic=(topic or "Summary")[:300], academic_level=req.academic_level,
            answer_length=req.length, output_style=req.style, document_id=req.document_id,
            result_json=json.dumps(result),
        )
        self.db.add(session)
        self.db.flush()  # assigns session.id
        self.db.add(Activity(activity_type="study", reference_id=session.id,
                             description=f"Study ({operation.replace('_', ' ')}): {label}"))
        self.db.commit()
        return {"session_id": session.id, "operation": operation, "result": result,
                "notes": notes, "sources": sources}