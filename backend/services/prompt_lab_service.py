"""Runnable demonstrations of each prompting technique, using real model calls."""
from backend.errors import AppError
from backend.models.lab_schemas import TopicCard
from backend.prompts.common import GROUNDING_RULES
from backend.prompts.prompt_lab_examples import FEW_SHOT_EXAMPLES, SAMPLE_CONTEXT, TECHNIQUES
from backend.services.prompt_service import BuiltPrompt, build_prompt
from backend.services.validation_service import extract_json

NOT_FOUND = "Not found in the provided context."


def _show(built: BuiltPrompt) -> str:
    return f"[SYSTEM]\n{built.system}\n\n[USER]\n{built.user}"


def _result(steps, final, validation=None):
    return {"steps": steps, "final_output": final, "validation": validation}


def _zero_shot(provider, topic):
    prompt = f"Explain the following topic in exactly three sentences for a first-year student.\n\nTopic: {topic}"
    out = provider.generate_text(prompt)
    return _result([{"label": "Zero-shot prompt (instruction only, no examples)", "prompt": prompt, "output": out}], out)


def _few_shot(provider, topic):
    built = build_prompt(
        role="a study-skills assistant who writes flashcards",
        task="Write one flashcard for the topic in USER INPUT, in exactly the same format as the examples.",
        examples=FEW_SHOT_EXAMPLES,
        constraints=["Output only the flashcard (a Q: line and an A: line)."],
        user_input=f"Topic: {topic}",
    )
    out = provider.generate_text(built.user, system=built.system)
    return _result([{"label": "Few-shot prompt (two worked examples)", "prompt": _show(built), "output": out}], out)


def _role(provider, topic):
    task = f"Explain this topic in three sentences: {topic}"
    role = ("You are a strict university examiner writing a model answer. Use precise terminology "
            "and finish with one common student mistake.")
    plain = provider.generate_text(task)
    roled = provider.generate_text(task, system=role)
    return _result([
        {"label": "Without a role", "prompt": task, "output": plain},
        {"label": "With a role (examiner)", "prompt": f"[SYSTEM]\n{role}\n\n[USER]\n{task}", "output": roled},
    ], roled)


def _chaining(provider, topic):
    p1 = (f"List the 3 most important concepts a student must know about: {topic}. "
          "Return one concept per line, with no numbering and no extra text.")
    out1 = provider.generate_text(p1)
    p2 = f"For each concept below, write one short exam question.\n\nConcepts:\n{out1}"
    out2 = provider.generate_text(p2)
    return _result([
        {"label": "Step 1: extract key concepts", "prompt": p1, "output": out1},
        {"label": "Step 2: questions from step 1's output", "prompt": p2, "output": out2},
    ], out2)


def _card_prompt(topic):
    return build_prompt(
        role="an expert tutor",
        rules=GROUNDING_RULES,
        task="Create a study card for the topic in USER INPUT.",
        output_schema=TopicCard,
        user_input=f"Topic: {topic}",
    )


def _structured(provider, topic):
    built = _card_prompt(topic)
    card = provider.generate_structured(built.user, TopicCard, system=built.system)
    final = card.model_dump_json(indent=2)
    return _result([{"label": "Schema-constrained prompt", "prompt": _show(built), "output": final}], final,
                   {"valid": True, "attempts": 1, "errors": [], "max_attempts": 3, "schema": "TopicCard"})


def _context_aware(provider, question):
    built = build_prompt(
        role="a teaching assistant who answers only from supplied context",
        rules=GROUNDING_RULES,
        document_context=SAMPLE_CONTEXT,
        task=("Answer the question in USER INPUT using only the DOCUMENT CONTEXT. If the context does not "
              f"contain the answer, reply exactly: {NOT_FOUND}"),
        user_input=question,
    )
    out = provider.generate_text(built.user, system=built.system)
    return _result([{"label": "Grounded prompt (context fenced as untrusted data)",
                     "prompt": _show(built), "output": out}], out)


def _validate_card(raw: str):
    try:
        return TopicCard.model_validate(extract_json(raw)), None
    except ValueError as exc:
        return None, str(exc)[:400]


def _validation(provider, topic):
    built = _card_prompt(topic)
    raw = provider.generate_text(built.user, system=built.system, json_mode=True)
    steps = [{"label": "Attempt 1: generate JSON", "prompt": _show(built), "output": raw}]
    card, err = _validate_card(raw)
    errors, attempts = [], 1
    if err:
        errors.append(err)
        repair = (f"{built.user}\n\n---\nYour previous reply was invalid.\nProblem: {err}\n"
                  f"Previous reply (truncated):\n{raw[:1500]}\n\n"
                  "Return ONLY corrected JSON that matches the schema.")
        raw = provider.generate_text(repair, system=built.system, json_mode=True)
        attempts = 2  # hard limit: one repair, then stop
        steps.append({"label": "Attempt 2: repair request", "prompt": repair, "output": raw})
        card, err = _validate_card(raw)
        if err:
            errors.append(err)
    final = card.model_dump_json(indent=2) if card else raw
    return _result(steps, final, {"valid": card is not None, "attempts": attempts, "errors": errors,
                                  "max_attempts": 2, "schema": "TopicCard"})


RUNNERS = {
    "zero_shot": _zero_shot, "few_shot": _few_shot, "role": _role, "chaining": _chaining,
    "structured": _structured, "context_aware": _context_aware, "validation": _validation,
}


def list_techniques() -> list[dict]:
    return TECHNIQUES


def run_technique(provider, technique_id: str, user_input: str) -> dict:
    spec = next((t for t in TECHNIQUES if t["id"] == technique_id), None)
    if not spec:
        raise AppError("Unknown technique.", 404)
    text = user_input.strip() or spec["default_input"]
    data = RUNNERS[technique_id](provider, text)
    return {"technique_id": technique_id, "name": spec["name"], "input": text,
            "model": provider.model, **data}