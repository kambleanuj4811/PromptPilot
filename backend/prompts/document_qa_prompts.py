from backend.models.ai_outputs import QAModelOutput
from backend.prompts.common import GROUNDING_RULES
from backend.services.prompt_service import BuiltPrompt, build_prompt

QA_ROLE = "a careful teaching assistant who answers strictly from supplied document passages"

QA_RULES = GROUNDING_RULES + [
    "Answer only with information found in the numbered passages.",
    "If the passages do not contain the answer, set sufficient_evidence to false and say what is missing. Do not guess.",
    "Do not mention page numbers or file names yourself; the system adds them.",
]


def build_qa_prompt(question: str, passages_text: str) -> BuiltPrompt:
    return build_prompt(
        role=QA_ROLE,
        rules=QA_RULES,
        document_context=passages_text,
        task="Answer the user's question using only the numbered passages in the DOCUMENT CONTEXT.",
        constraints=[
            "Put the direct answer in 'answer'.",
            "In 'evidence', list up to 3 items. Each has 'source' (the passage number) and 'quote', "
            "copied EXACTLY, word for word, from that passage (at most 30 words).",
            "Put any reasoning or interpretation in 'explanation', separate from the quoted evidence.",
        ],
        output_schema=QAModelOutput,
        user_input=question,
    )