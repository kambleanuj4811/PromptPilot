from backend.services.prompt_service import FewShotExample

SAMPLE_CONTEXT = (
    "Mitochondria are organelles found in most eukaryotic cells. They produce most of the cell's ATP "
    "through cellular respiration. A mitochondrion has a double membrane, and its inner membrane is "
    "folded into structures called cristae. Mitochondria also contain their own small circular DNA."
)

FEW_SHOT_EXAMPLES = [
    FewShotExample(
        input="Topic: Osmosis",
        output="Q: What is osmosis?\nA: The movement of water across a semi-permeable membrane from a "
               "region of lower solute concentration to higher solute concentration.",
    ),
    FewShotExample(
        input="Topic: Photosynthesis",
        output="Q: What does photosynthesis produce?\nA: Glucose and oxygen, made from carbon dioxide "
               "and water using light energy.",
    ),
]

TECHNIQUES = [
    {
        "id": "zero_shot", "name": "Zero-shot prompting", "model_calls": 1,
        "explanation": "The model gets only an instruction, with no examples. It relies on what it already knows.",
        "example_prompt": "Explain the following topic in exactly three sentences for a first-year student.\n\nTopic: {topic}",
        "why": "It is the simplest and cheapest approach and the baseline every other technique is compared with.",
        "input_label": "Topic", "default_input": "How vaccines work", "input_hint": "",
    },
    {
        "id": "few_shot", "name": "Few-shot prompting", "model_calls": 1,
        "explanation": "The prompt includes worked examples so the model copies their format and style.",
        "example_prompt": "EXAMPLES:\nExample 1 input: Topic: Osmosis\nExample 1 output: Q: ... A: ...\n\nTASK: Write a flashcard for the topic.\n\nUSER INPUT: Topic: {topic}",
        "why": "Examples fix the output format far more reliably than describing it in words.",
        "input_label": "Topic", "default_input": "Mitosis", "input_hint": "",
    },
    {
        "id": "role", "name": "Role prompting", "model_calls": 2,
        "explanation": "A system instruction gives the model a persona. This demo runs the same task with and without one.",
        "example_prompt": "[SYSTEM] You are a strict university examiner writing a model answer...\n[USER] Explain this topic in three sentences: {topic}",
        "why": "A role sets tone, vocabulary and level of rigor, so outputs fit the audience.",
        "input_label": "Topic", "default_input": "How vaccines work", "input_hint": "",
    },
    {
        "id": "chaining", "name": "Prompt chaining", "model_calls": 2,
        "explanation": "A task is split into steps, and the output of one prompt becomes the input of the next.",
        "example_prompt": "Step 1: List the 3 key concepts of {topic}.\nStep 2: For each concept below, write one exam question.\n[Step 1 output inserted here]",
        "why": "Smaller focused prompts are easier to control and debug than one huge prompt.",
        "input_label": "Topic", "default_input": "Newton's laws of motion", "input_hint": "",
    },
    {
        "id": "structured", "name": "Structured JSON output", "model_calls": 1,
        "explanation": "The prompt includes a JSON schema, and the reply is parsed and validated against a Pydantic model.",
        "example_prompt": "OUTPUT FORMAT: Return JSON matching this schema: {title, definition, key_points[2-5], difficulty}\n\nUSER INPUT: Topic: {topic}",
        "why": "Structured output lets the application display results reliably instead of parsing free text.",
        "input_label": "Topic", "default_input": "Binary search", "input_hint": "",
    },
    {
        "id": "context_aware", "name": "Context-aware prompting", "model_calls": 1,
        "explanation": "The model answers only from supplied text, which is fenced as untrusted data. It must say when the context lacks the answer.",
        "example_prompt": "DOCUMENT CONTEXT: <<<DOCUMENT START ...>>>\n\nTASK: Answer using only the context. If missing, say: Not found in the provided context.\n\nUSER INPUT: {question}",
        "why": "Grounding in supplied text reduces hallucination. This is the idea behind document Q&A.",
        "input_label": "Question about the sample passage", "default_input": "What do mitochondria produce?",
        "input_hint": "Try an unanswerable question such as: Who discovered mitochondria?",
    },
    {
        "id": "validation", "name": "Output validation and repair", "model_calls": 2,
        "explanation": "The reply is validated against a schema. If invalid, the app sends one repair request, then stops.",
        "example_prompt": "[Attempt 1] Return JSON for {topic}\n[If invalid] Your previous reply was invalid. Problem: ... Return ONLY corrected JSON.",
        "why": "Models sometimes break the format. Validation plus a capped retry makes the pipeline dependable without infinite loops.",
        "input_label": "Topic", "default_input": "Hash tables", "input_hint": "",
    },
]