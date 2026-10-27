from backend.models import ai_outputs as o
from backend.prompts.common import GROUNDING_RULES
from backend.services.prompt_service import BuiltPrompt, FewShotExample, build_prompt

STUDY_ROLE = "an expert academic tutor who writes accurate, well-organised study material"

LEVEL_GUIDE = {
    "school": "high-school students",
    "undergraduate": "undergraduate students",
    "postgraduate": "postgraduate students",
    "professional": "working professionals",
}
STYLE_GUIDE = {
    "simple": "plain, simple language with everyday analogies",
    "exam": "concise, exam-oriented phrasing with correct terminology",
    "technical": "precise technical language",
}
LENGTH_GUIDE = {
    "short": "about 100-150 words in total",
    "medium": "about 250-350 words in total",
    "detailed": "about 500-700 words in total",
}

# Few-shot example: one MCQ shows the exact structure and the style of explanation.
MCQ_EXAMPLE = FewShotExample(
    input="Topic: The water cycle (1 question)",
    output=(
        '{"questions": [{"question": "Which process turns water vapour into liquid droplets?", '
        '"options": ["Evaporation", "Condensation", "Precipitation", "Transpiration"], '
        '"correct_index": 1, "explanation": "Condensation is the cooling of vapour into liquid '
        'droplets, which forms clouds."}]}'
    ),
)

OPERATIONS = {
    "explain": dict(
        schema=o.ExplainOutput, uses_length=True, label="Topic: ",
        task="Explain the topic given in USER INPUT so a student can learn it.",
    ),
    "summarize": dict(
        schema=o.SummaryOutput, uses_length=True, label="Focus (optional): ",
        task="Summarize the material in the DOCUMENT CONTEXT.",
    ),
    "revision_notes": dict(
        schema=o.RevisionOutput, uses_length=True, label="Topic: ",
        task="Create concise revision notes on the topic in USER INPUT, as headed sections of short points.",
    ),
    "mcqs": dict(
        schema=o.MCQOutput, uses_length=False, label="Topic: ", examples=[MCQ_EXAMPLE],
        task=("Write exactly {count} multiple-choice questions on the topic in USER INPUT. Each has "
              "exactly 4 distinct options, one correct answer (correct_index 0-3) and a short explanation."),
    ),
    "questions": dict(
        schema=o.ShortQuestionsOutput, uses_length=False, label="Topic: ",
        task=("Write exactly {count} short-answer exam questions on the topic in USER INPUT, each with "
              "a model answer and a marks value from 1 to 10."),
    ),
    "exam_answer": dict(
        schema=o.ExamAnswerOutput, uses_length=True, label="Exam question: ",
        task=("Write a model exam-ready answer to the exam question in USER INPUT: an introduction, "
              "headed body sections, a conclusion and key terms."),
    ),
}


def build_study_prompt(operation, *, topic, level, length, style, count, context):
    spec = OPERATIONS[operation]
    rules = list(GROUNDING_RULES)
    if context:
        rules.append("Base the output on the DOCUMENT CONTEXT. If it does not cover something, leave it "
                     "out rather than inventing it.")
    constraints = [f"Write for {LEVEL_GUIDE[level]}.", f"Use {STYLE_GUIDE[style]}."]
    if spec["uses_length"]:
        constraints.append(f"Length: {LENGTH_GUIDE[length]}.")
    built: BuiltPrompt = build_prompt(
        role=STUDY_ROLE,
        task=spec["task"].format(count=count),
        rules=rules,
        document_context=context,
        examples=spec.get("examples"),
        constraints=constraints,
        output_schema=spec["schema"],
        user_input=f"{spec['label']}{topic}" if topic else None,
    )
    return built, spec["schema"]