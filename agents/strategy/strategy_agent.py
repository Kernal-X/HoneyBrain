"""
Strategy Agent — translates Analysis output into an executable deception strategy.
"""

from __future__ import annotations

import os
from typing import Any, Dict

from utils.llm_client import call_openai_strategy_llm

from .parser import parse_strategy_response
from .prompt_builder import build_deterministic_hints, build_strategy_prompt
from .schema import compute_generation_limits, confidence_to_strategy_type, stage_to_depth
from .validator import (
    apply_deterministic_overrides,
    build_fallback_strategy,
    enforce_safety_and_tags,
    normalize_strategy_enumerations,
    trim_execution_to_limits,
    validate_strategy_shape,
)


# This function defines the SAFE ZONE where your deception system lives
def _staging_root() -> str:
    env = os.environ.get("DECOY_STAGING_ROOT")  # checking environment variables    
    if env:
        return os.path.abspath(env.strip())
    # If user/system explicitly defines a custom path → use it
    if os.name == "nt":
        base = os.environ.get("ProgramData", r"C:\ProgramData")
        return os.path.abspath(os.path.join(base, "DeceptionLab", "staging"))
    # windows default path
    # Use C:\ProgramData\DeceptionLab\staging
    return os.path.abspath(os.path.join("/var/lib", "deception", "staging"))
    # Linux Unix default path
    #Use /var/lib/deception/staging


def strategy_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input: state['analysis'] with intent, attack_stage, confidence, reasoning.
    Output: state['strategy'] full executable plan for the Generation Agent.
    """
    analysis = state.get("analysis")
    if not isinstance(analysis, dict):
        analysis = {
            "intent": "unknown",
            "attack_stage": "unknown",
            "confidence": 0.0,
            "reasoning": ["missing analysis; defaulted"],
        }
        state["analysis"] = analysis
    # Input Extraction + Defaulting

    staging = _staging_root()   # determine where fake artifacts will live
    hints = build_deterministic_hints(analysis, staging)
    prompt = build_strategy_prompt(analysis, hints, staging)

    raw: str | None = None
    try:
        raw = call_openai_strategy_llm(prompt)
        parsed = parse_strategy_response(raw)
    except Exception as exc:
        print(f"Strategy LLM or parse failed ({exc}); using deterministic fallback.")
        state["strategy"] = build_fallback_strategy(analysis, staging)
        state["strategy_meta"] = {"source": "fallback", "error": str(exc)}
        return state

    merged = apply_deterministic_overrides(parsed, analysis)
    merged = normalize_strategy_enumerations(merged, analysis)
    merged = enforce_safety_and_tags(merged)

    stype = str(merged.get("strategy_type", confidence_to_strategy_type(float(analysis.get("confidence", 0)))))
    depth = str(merged.get("placement_plan", {}).get("depth", stage_to_depth(str(analysis.get("attack_stage", "unknown")))))
    max_files, max_credentials = compute_generation_limits(stype, depth)
    merged = trim_execution_to_limits(merged, max_files, max_credentials)

    ok, errors = validate_strategy_shape(merged, analysis, max_files, max_credentials)
    if not ok:
        print("Strategy validation failed:", "; ".join(errors))
        state["strategy"] = build_fallback_strategy(analysis, staging)
        state["strategy_meta"] = {"source": "fallback_validation", "errors": errors, "raw_preview": (raw or "")[:800]}
        return state

    state["strategy"] = merged
    state["strategy_meta"] = {"source": "llm", "model": "gpt-4o-mini"}
    return state
