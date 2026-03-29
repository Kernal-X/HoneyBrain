# core/decision_engine.py

def decide_action(path, metadata, rules, state, supported_types):

    risk_score = state.get("risk_score", 0.0)
    intent = state.get("intent", "unknown")

    file_type = metadata.get("file_type", "txt")

    # unsupported → real
    if file_type not in supported_types:
        return "real"

    rule = rules.get(path, {})
    threshold = rule.get("risk_threshold", 0.7)
    mode = rule.get("deception_mode", "partial")

    if risk_score < 0.3:
        return "real"

    if risk_score < threshold:
        return "partial" if mode == "partial" else "real"

    if intent in ["data_exfiltration", "reconnaissance"]:
        return "fake"

    return "fake" if mode == "full" else "real"