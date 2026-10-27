"""Document Q&A: scope -> retrieve -> prompt -> generate -> verify -> respond."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.errors import AppError
from backend.models.ai_outputs import QAModelOutput
from backend.models.database_models import Activity, Document
from backend.prompts.document_qa_prompts import build_qa_prompt
from backend.services.context_service import (
    chunk_to_source, format_chunks, get_ready_document, normalize,
)

TOP_K = 5
MIN_SCORE = 0.15  # cosine similarity floor; below this a passage is treated as unrelated
DISCLAIMER = "AI-generated answer. Check the quoted evidence against your document."


class QAService:
    def __init__(self, db: Session, provider, embedder, retrieval):
        self.db, self.provider, self.embedder, self.retrieval = db, provider, embedder, retrieval

    def _scope(self, document_ids: list[str] | None) -> list[str]:
        if document_ids:
            return [get_ready_document(self.db, d).id for d in dict.fromkeys(document_ids)]
        ready = list(self.db.scalars(select(Document.id).where(Document.status == "ready")))
        if not ready:
            raise AppError("Upload a document first, then ask questions about it.", 400)
        return ready

    @staticmethod
    def _verify(model_out: QAModelOutput, hits) -> list[dict]:
        """Keep only quotes that really appear in the cited retrieved passage."""
        verified = []
        for ev in model_out.evidence:
            if not 1 <= ev.source <= len(hits):
                continue
            quote = normalize(ev.quote)
            hit = hits[ev.source - 1]
            if len(quote) >= 10 and quote in normalize(hit.text):
                verified.append({
                    "source": ev.source, "document_id": hit.document_id, "filename": hit.filename,
                    "page_number": hit.page_number, "quote": ev.quote.strip(),
                })
        return verified

    def ask(self, question: str, document_ids: list[str] | None) -> dict:
        scope = self._scope(document_ids)
        qvec = self.embedder.embed([question])[0]
        hits = [h for h in self.retrieval.search(qvec, scope, TOP_K) if h.score >= MIN_SCORE]

        if not hits:  # nothing relevant: do not even call the model
            return self._respond(
                "insufficient_evidence",
                "I could not find passages in the selected documents that relate to this question.",
                [], "", [], question,
            )

        built = build_qa_prompt(question, format_chunks(hits))
        out = self.provider.generate_structured(built.user, QAModelOutput, system=built.system)
        verified = self._verify(out, hits)
        if not out.sufficient_evidence:
            status = "insufficient_evidence"
        elif not verified:
            status = "unverified"
        else:
            status = "answered"
        cited = {v["source"] for v in verified}
        sources = [chunk_to_source(i, h, cited=i in cited) for i, h in enumerate(hits, 1)]
        return self._respond(status, out.answer, verified, out.explanation, sources, question)

    def _respond(self, status, answer, evidence, explanation, sources, question) -> dict:
        self.db.add(Activity(activity_type="document_qa", description=f"Asked: {question[:80]}"))
        self.db.commit()
        data = {
            "status": status, "answer": answer, "evidence": evidence,
            "explanation": explanation,  # model-generated interpretation, kept separate from evidence
            "sources": sources, "disclaimer": DISCLAIMER,
        }
        if status == "unverified":
            data["warning"] = ("The answer's quotes could not be matched to the document text. "
                               "Treat it as unverified.")
        return data