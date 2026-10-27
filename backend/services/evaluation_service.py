"""Prompt comparison: run both prompts -> deterministic checks -> LLM judge -> aggregate -> save."""
import json
from statistics import mean

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.errors import AppError
from backend.models.database_models import Activity, EvaluationResult, PromptEvaluation
from backend.models.eval_schemas import CompareRequest, JudgeOutput
from backend.prompts.evaluation_prompts import build_judge_prompt
from backend.services.ai_provider import AIInvalidResponseError

CRITERIA = ["accuracy", "completeness", "relevance", "consistency", "formatting"]
WINNER_MARGIN = 0.5
DISCLAIMER = (
    "Scores are estimates produced by an AI judge. LLM judges can be biased, can vary between runs, "
    "and may miss factual errors. Consistency is judged within each response, not across questions. "
    "Automatic format checks (when you set format rules) are exact."
)


def has_rules(req: CompareRequest) -> bool:
    return req.expected_format == "json" or req.max_words is not None


def run_checks(output: str, expected_format: str, required_fields: list[str],
               max_words: int | None) -> list[dict]:
    non_empty = bool(output.strip())
    checks = [{"name": "non_empty", "passed": non_empty,
               "detail": "Response is not empty." if non_empty else "Response is empty."}]
    if expected_format == "json":
        parsed = None
        try:
            parsed = json.loads(output.strip())
            valid, detail = True, "Valid raw JSON."
        except ValueError:
            valid, detail = False, "Not valid raw JSON (code fences or extra text count as invalid)."
        checks.append({"name": "valid_json", "passed": valid, "detail": detail})
        if required_fields:
            if isinstance(parsed, dict):
                missing = [f for f in required_fields if f not in parsed]
                checks.append({"name": "required_fields", "passed": not missing,
                               "detail": "All required fields present." if not missing
                               else "Missing fields: " + ", ".join(missing)})
            else:
                checks.append({"name": "required_fields", "passed": False,
                               "detail": "Output is not a JSON object, so required fields cannot be present."})
    if max_words is not None:
        n = len(output.split())
        checks.append({"name": "max_words", "passed": n <= max_words,
                       "detail": f"{n} words (limit {max_words})."})
    return checks


def formatting_from_checks(checks: list[dict]) -> dict:
    rule_checks = [c for c in checks if c["name"] != "non_empty"]
    passed = sum(c["passed"] for c in rule_checks)
    return {
        "score": round(10 * passed / len(rule_checks), 1),
        "justification": f"Computed from {len(rule_checks)} automatic check(s); {passed} passed.",
        "issues": [c["detail"] for c in rule_checks if not c["passed"]],
    }


def aggregate(rows: list[dict]) -> dict:
    variants = {}
    for v in ("A", "B"):
        mine = [r for r in rows if r["variant"] == v]
        scored = [r for r in mine if r["scores"]]
        variants[v] = {
            "scored": len(scored), "total": len(mine),
            "criteria": ({c: round(mean(r["scores"][c]["score"] for r in scored), 1) for c in CRITERIA}
                         if scored else None),
            "overall": round(mean(r["overall"] for r in scored), 1) if scored else None,
        }
    a, b = variants["A"]["overall"], variants["B"]["overall"]
    if a is None or b is None:
        winner, margin = "unavailable", None
    else:
        margin = round(a - b, 1)
        winner = "tie" if abs(margin) < WINNER_MARGIN else ("A" if margin > 0 else "B")
    notes = []
    unscored = sum(v["total"] - v["scored"] for v in variants.values())
    if unscored:
        notes.append(f"{unscored} response(s) could not be scored and are excluded from the averages.")
        if variants["A"]["scored"] != variants["B"]["scored"]:
            notes.append("A and B averages cover different numbers of questions; compare with care.")
    return {"variants": variants, "winner": winner, "margin": margin, "notes": notes,
            "winner_margin_rule": f"A winner needs an overall difference of at least {WINNER_MARGIN}."}


class EvaluationService:
    def __init__(self, db: Session, provider):
        self.db, self.provider = db, provider

    @staticmethod
    def _format_rules(req: CompareRequest) -> str | None:
        parts = []
        if req.expected_format == "json":
            parts.append("response must be raw JSON only")
        if req.required_fields:
            parts.append("required JSON fields: " + ", ".join(req.required_fields))
        if req.max_words is not None:
            parts.append(f"at most {req.max_words} words")
        return "; ".join(parts) or None

    def _generate(self, prompt: str, question: str) -> tuple[str, str | None]:
        try:
            return self.provider.generate_text(question, system=prompt), None
        except AIInvalidResponseError as exc:  # empty or blocked response
            return "", exc.message

    def _judge(self, req, question, prompt, output, checks):
        built = build_judge_prompt(question, prompt, output, self._format_rules(req))
        try:
            out = self.provider.generate_structured(built.user, JudgeOutput, system=built.system)
        except AIInvalidResponseError as exc:
            return None, exc.message
        criteria = {c: getattr(out, c).model_dump() for c in CRITERIA}
        if has_rules(req):
            criteria["formatting"] = formatting_from_checks(checks)
        return criteria, None

    def compare(self, req: CompareRequest) -> dict:
        rows = []
        for qi, question in enumerate(req.test_questions):
            for variant, prompt in (("A", req.prompt_a), ("B", req.prompt_b)):
                output, error = self._generate(prompt, question)
                checks = run_checks(output, req.expected_format, req.required_fields, req.max_words)
                scores = None
                if output.strip():
                    scores, error = self._judge(req, question, prompt, output, checks)
                else:
                    error = error or "The AI returned an empty response."
                overall = round(mean(scores[c]["score"] for c in CRITERIA), 1) if scores else None
                rows.append({"question_index": qi, "question": question, "variant": variant,
                             "output": output, "checks": checks, "scores": scores,
                             "overall": overall, "error": error})

        summary = aggregate(rows)
        summary["settings"] = {"expected_format": req.expected_format,
                               "required_fields": req.required_fields, "max_words": req.max_words,
                               "question_count": len(req.test_questions)}
        # Nothing is saved until every AI call has finished, so a quota error leaves no partial record.
        ev = PromptEvaluation(prompt_a=req.prompt_a, prompt_b=req.prompt_b, summary_json=json.dumps(summary))
        self.db.add(ev)
        self.db.flush()
        for r in rows:
            self.db.add(EvaluationResult(
                evaluation_id=ev.id, test_input=r["question"], variant=r["variant"], output=r["output"],
                scores_json=json.dumps({"criteria": r["scores"], "error": r["error"]}),
                deterministic_json=json.dumps({"question_index": r["question_index"], "checks": r["checks"]}),
                overall_score=r["overall"]))
        self.db.add(Activity(activity_type="evaluation", reference_id=ev.id,
                             description=f"Compared prompts on {len(req.test_questions)} question(s)"))
        self.db.commit()
        return self._detail(ev)

    def _detail(self, ev: PromptEvaluation) -> dict:
        by_q: dict[int, dict] = {}
        for r in ev.results:
            det, sc = json.loads(r.deterministic_json), json.loads(r.scores_json)
            entry = by_q.setdefault(det["question_index"],
                                    {"question_index": det["question_index"], "question": r.test_input})
            entry[r.variant.lower()] = {"output": r.output, "checks": det["checks"],
                                        "scores": sc["criteria"], "overall": r.overall_score,
                                        "error": sc["error"]}
        return {"id": ev.id, "created_at": ev.created_at.isoformat(),
                "prompt_a": ev.prompt_a, "prompt_b": ev.prompt_b,
                "results": [by_q[k] for k in sorted(by_q)],
                "summary": json.loads(ev.summary_json), "disclaimer": DISCLAIMER}

    def history(self) -> list[dict]:
        rows = self.db.scalars(
            select(PromptEvaluation).order_by(PromptEvaluation.created_at.desc()).limit(50))
        out = []
        for ev in rows:
            s = json.loads(ev.summary_json)
            out.append({"id": ev.id, "created_at": ev.created_at.isoformat(),
                        "prompt_a": ev.prompt_a[:120], "prompt_b": ev.prompt_b[:120],
                        "question_count": s["settings"]["question_count"], "winner": s["winner"],
                        "overall_a": s["variants"]["A"]["overall"], "overall_b": s["variants"]["B"]["overall"]})
        return out

    def get(self, evaluation_id: str) -> dict:
        ev = self.db.get(PromptEvaluation, evaluation_id)
        if not ev:
            raise AppError("Evaluation not found.", 404)
        return self._detail(ev)