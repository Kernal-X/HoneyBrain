# core/context_builder.py

def build_interception_input(event, aggregated_state, analysis_output, deployment_state):

    return {
        "path": event["data"].get("path"),
        "user": event["data"].get("user"),
        "process": event["data"].get("process"),
        "timestamp": event.get("timestamp"),

        "aggregated_state": {
            "risk_score": aggregated_state.get("risk_score", 0.0),
            "attack_stage": analysis_output.get("attack_stage", "unknown"),
            "intent": analysis_output.get("intent", "unknown")
        },

        "deployment": deployment_state
    }