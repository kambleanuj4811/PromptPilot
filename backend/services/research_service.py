"""Research Mode: gather aspect-relevant passages, call the model, then verify quotes in code."""
from sqlalchemy.orm import Session

from backend.errors import AppError
from backend.models.database_models import Activity
from backend.models.research_schemas import ResearchAnalysisOutput, ResearchSummaryOutput
from backend.prompts.research_prompts import build_analysis_prompt, build_summary_prompt
from backend.services.context_service import (
    chunk_to_source, format_chunks, get_ready_document, normalize,
)

ASPECT_QUERIES = [
    "research objectives aim purpose of this study hypothesis",
    "methodology methods approach experimental setup dataset procedure",
    "results findings key outcomes performance evaluation",
    "limitations threats to validity future work weaknesses",
    "conclusion summary contributions implications",
]
ASPECT_KEYS = ["objectives", "methodology", "key_findings", "limitations", "conclusions"]
MIN_SCORE = 0.15
PER_QUERY = 3
MAX_CHUNKS = 12
DISCLAIMER = (
    "AI-generated. Listed findings include only quotes verified in the document; the overview, "
    "summary and interpretations are model-generated."
)


class ResearchService:
    def __init__(self, db: Session, provider, embedder, retrieval):
        self.db, self.provider, self.embedder, self.retrieval = db, provider, embedder, retrieval

    def _gather(self, document_id: str):
        doc = get_ready_document(self.db, document_id)
        picked = {}
        for vec in self.embedder.embed(ASPECT_QUERIES):
            for hit in self.retrieval.search(vec, [doc.id], PER_QUERY):
                if hit.score >= MIN_SCORE:
                    picked[hit.chunk_index] = hit
        if not picked:
            raise AppError("No relevant paper content was found in this document.", 422)
        best = sorted(picked.values(), key=lambda h: -h.score)[:MAX_CHUNKS]
        chunks = sorted(best, key=lambda h: h.chunk_index)  # reading order
        total = self.retrieval.count_for_document(doc.id)
        notes = []
        if len(chunks) < total:
            notes.append(f"Based on {len(chunks)} of {total} document sections (the ones matching "
                         "typical paper topics). Other sections were not read.")
        return doc, chunks, notes

    @staticmethod
    def _verify_aspect(aspect: dict, chunks) -> tuple[dict, int]:
        kept, dropped = [], 0
        for f in aspect["findings"]:
            src, quote = f["source"], normalize(f["quote"])
            if 1 <= src <= len(chunks) and len(quote) >= 10 and quote in normalize(chunks[src - 1].text):
                c = chunks[src - 1]
                kept.append({"statement": f["statement"], "quote": f["quote"].strip(),
                             "filename": c.filename, "page_number": c.page_number, "source": src})
            else:
                dropped += 1
        return ({"found_in_document": bool(kept), "findings": kept,
                 "interpretation": aspect["interpretation"]}, dropped)

    def analyze(self, document_id: str) -> dict:
        doc, chunks, notes = self._gather(document_id)
        built = build_analysis_prompt(format_chunks(chunks))
        data = self.provider.generate_structured(
            built.user, ResearchAnalysisOutput, system=built.system).model_dump()
        analysis, dropped_total = {"overview": data["overview"]}, 0
        for key in ASPECT_KEYS:
            analysis[key], dropped = self._verify_aspect(data[key], chunks)
            dropped_total += dropped
        if dropped_total:
            notes.append(f"{dropped_total} AI-reported statement(s) were removed because their quotes "
                         "could not be found in the document text.")
        return self._respond(doc, "analysis", analysis, notes, chunks, "Analysed paper")

    def summarize(self, document_id: str) -> dict:
        doc, chunks, notes = self._gather(document_id)
        built = build_summary_prompt(format_chunks(chunks))
        out = self.provider.generate_structured(
            built.user, ResearchSummaryOutput, system=built.system).model_dump()
        return self._respond(doc, "summary", out, notes, chunks, "Summarised paper")

    def _respond(self, doc, key, result, notes, chunks, verb) -> dict:
        self.db.add(Activity(activity_type="research", reference_id=doc.id,
                             description=f"{verb}: {doc.original_filename}"[:300]))
        self.db.commit()
        return {
            "document": {"id": doc.id, "filename": doc.original_filename},
            key: result, "notes": notes,
            "sources": [chunk_to_source(i, c) for i, c in enumerate(chunks, 1)],
            "disclaimer": DISCLAIMER,
        }