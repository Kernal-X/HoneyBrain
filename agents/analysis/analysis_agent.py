from .formatter import format_events
from .prompt_builder import build_prompt
from .parser import parse_response,normalize_output
from .validator import sanitize_output
from utils.llm_client import call_llm


def analysis_agent(state):
    risk_score = state.get("risk_score", 0)
    events = state.get("events", [])

    formatted = format_events(events)

    prompt = build_prompt(risk_score, formatted)

    raw_output = call_llm(prompt)

    parsed = parse_response(raw_output)

    normalized = normalize_output(parsed)

    cleaned = sanitize_output(normalized)

    state["analysis"] = cleaned

    return state