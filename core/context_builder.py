# core/context_builder.py

def build_interception_input(event, analysis_output, deployment_state):

    return {
        "path": event["data"].get("path"),
        "user": event["data"].get("user"),
        "process": event["data"].get("process"),
        "timestamp": event.get("timestamp"),

        "analysis": {
            "attack_stage": analysis_output.get("attack_stage", "unknown"),
            "intent": analysis_output.get("intent", "unknown"),
            "confidence": analysis_output.get("confidence", 0.0)
        },

        "deployment": deployment_state
    }