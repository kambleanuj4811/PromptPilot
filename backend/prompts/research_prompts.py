from backend.models.research_schemas import ResearchAnalysisOutput, ResearchSummaryOutput
from backend.prompts.common import GROUNDING_RULES
from backend.services.prompt_service import build_prompt

RESEARCH_ROLE = "a meticulous research assistant who reads academic papers and reports only what the text supports"

RESEARCH_RULES = GROUNDING_RULES + [
    "Never invent experimental results, statistics, citations, datasets, or findings.",
    "Clearly separate what the document states from your own interpretation.",
    "The passages are excerpts, not the whole paper. If something is not covered in them, say so.",
]


def build_analysis_prompt(context: str):
    return build_prompt(
        role=RESEARCH_ROLE,
        rules=RESEARCH_RULES,
        document_context=context,
        task="Analyse the paper excerpts in the DOCUMENT CONTEXT and fill in every field of the schema.",
        constraints=[
            "overview: 2-4 sentences summarising the excerpts. This is your own summary.",
            "For each aspect (objectives, methodology, key_findings, limitations, conclusions) list up to "
            "3 findings. 'statement' paraphrases what the document says; 'quote' is copied EXACTLY, word "
            "for word, from the cited passage (at most 30 words); 'source' is the passage number.",
            "If the excerpts do not clearly state an aspect, set found_in_document to false, leave "
            "findings empty, and do not guess.",
            "Put limitations the authors state in 'findings'. A limitation you infer yourself goes only in "
            "'interpretation' and must be labelled as your inference.",
            "'interpretation' is optional, at most 2 sentences, and is your own reasoning, never "
            "presented as the paper's claim.",
        ],
        output_schema=ResearchAnalysisOutput,
    )


def build_summary_prompt(context: str):
    return build_prompt(
        role=RESEARCH_ROLE,
        rules=RESEARCH_RULES,
        document_context=context,
        task="Summarize the research paper excerpts in the DOCUMENT CONTEXT.",
        constraints=[
            "summary: 120-200 words covering purpose, approach, main results and conclusion, but only "
            "those the excerpts actually contain.",
            "key_points: 3-6 short bullet points.",
            "Do not add numbers, results or claims that are not in the excerpts.",
        ],
        output_schema=ResearchSummaryOutput,
    )