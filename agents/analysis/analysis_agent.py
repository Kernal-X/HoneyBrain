from .context_builder import build_context
from .prompt_builder import build_prompt
from .parser import parse_response
from .validator import validate_output, sanitize_intent, clamp_confidence
from utils.llm_client import call_llm


def safe_llm_call(prompt):
    for _ in range(2):
        raw_output = call_llm(prompt)
        # print("\n--- RAW LLM OUTPUT ---")
        # print(raw_output)
        parsed = parse_response(raw_output)

        if validate_output(parsed):
            return parsed

    return {
        "attack_stage": "unknown",
        "intent": "unknown",
        "confidence": 0.0,
        "reasoning": ["fallback triggered"]
    }


def analysis_agent(input_data):
    context = build_context(input_data)
    prompt = build_prompt(context)

    parsed_output = safe_llm_call(prompt)

    # sanitize output
    parsed_output["intent"] = sanitize_intent(parsed_output["intent"])
    parsed_output["confidence"] = clamp_confidence(parsed_output["confidence"])
    parsed_output["reasoning"] = parsed_output["reasoning"][:2]

    return parsed_output