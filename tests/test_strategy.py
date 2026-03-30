import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.strategy.schema import (
    compute_generation_limits,
    confidence_to_strategy_type,
    stage_to_depth,
)
from agents.strategy.strategy_agent import strategy_agent
from agents.strategy.validator import build_fallback_strategy, validate_strategy_shape
from agents.deception_graph import deception_workflow


def test_confidence_bands():
    assert confidence_to_strategy_type(0.8) == "targeted"
    assert confidence_to_strategy_type(0.5) == "hybrid"
    assert confidence_to_strategy_type(0.2) == "exploratory"


def test_stage_depth():
    assert stage_to_depth("initial_access") == "minimal_deception"
    assert stage_to_depth("exfiltration") == "high_deception"


def test_fallback_strategy_valid():
    os.environ.pop("OPENAI_API_KEY", None)
    analysis = {
        "intent": "data_exfiltration",
        "attack_stage": "collection",
        "confidence": 0.82,
        "reasoning": ["r1", "r2"],
    }
    fb = build_fallback_strategy(analysis, os.path.join(os.path.expanduser("~"), "decoy_test_staging"))
    st = str(fb.get("strategy_type"))
    depth = str(fb["placement_plan"]["depth"])
    mf, mc = compute_generation_limits(st, depth)
    ok, errs = validate_strategy_shape(fb, analysis, mf, mc)
    assert ok, errs
    assert fb["data_protection"]["real_files_lock"] is True
    assert fb["data_protection"]["backup_original_data"] is True


def test_strategy_agent_fallback_without_api_key():
    os.environ.pop("OPENAI_API_KEY", None)
    state = {
        "analysis": {
            "intent": "reconnaissance",
            "attack_stage": "execution",
            "confidence": 0.55,
            "reasoning": ["a", "b"],
        }
    }
    out = strategy_agent(state.copy())
    assert "strategy" in out
    assert out["strategy"]["strategy_type"] == "hybrid"
    assert out["strategy_meta"]["source"] == "fallback"


def test_deception_graph_invocation():
    os.environ.pop("OPENAI_API_KEY", None)
    init = {
        "risk_score": 0.7,
        "events": [
            {
                "type": "file",
                "data": {"file_path": "C:\\data\\secret.zip", "action": "read"},
            }
        ],
    }
    final = deception_workflow.invoke(init)
    assert "analysis" in final
    assert "strategy" in final
    assert "generation" in final
    assert final["generation"]["status"] == "queued"
