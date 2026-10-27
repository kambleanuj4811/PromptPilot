"""Helpers for parsing and validating model output."""
import json
import re
from typing import Any


def extract_json(raw: str) -> Any:
    """Pull a JSON value out of model text (handles code fences and chatter).

    Raises ValueError if no valid JSON can be found."""
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    starts = [i for i in (text.find("{"), text.find("[")) if i != -1]
    if not starts:
        raise ValueError("No JSON found in model output.")
    start = min(starts)
    end = max(text.rfind("}"), text.rfind("]"))
    if end <= start:
        raise ValueError("Incomplete JSON in model output.")
    return json.loads(text[start : end + 1])