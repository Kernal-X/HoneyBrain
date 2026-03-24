def build_context(input_data):
    return {
        "risk_score": input_data.risk_score,
        "signals": input_data.signals,
        "recent_events": input_data.events[-5:]
    }