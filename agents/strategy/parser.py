"""
Extract and parse JSON from LLM responses for the Strategy Agent.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict


def parse_strategy_response(response: str) -> Dict[str, Any]:
    """
    Safely extract a single JSON object from model output.
    """
    if not response or not str(response).strip():
        raise ValueError("empty model response")

    cleaned = re.sub(r"```(?:json)?\s*|```", "", str(response), flags=re.IGNORECASE).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", cleaned)
    if not match:
        raise ValueError("no JSON object found in model response")

    try:
        return json.loads(match.group())
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid JSON: {e}") from e
