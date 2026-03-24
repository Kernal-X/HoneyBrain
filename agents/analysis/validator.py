ALLOWED_INTENTS = [
    "credential_bruteforce",
    "data_exfiltration",
    "reconnaissance",
    "privilege_escalation"
]

def validate_output(output):
    required_keys = ["attack_stage", "intent", "confidence", "reasoning"]

    for key in required_keys:
        if key not in output:
            return False

    if not isinstance(output["confidence"], (int, float)):
        return False

    if not isinstance(output["reasoning"], list):
        return False

    return True


def sanitize_intent(intent):
    return intent if intent in ALLOWED_INTENTS else "unknown"


def clamp_confidence(conf):
    try:
        conf = float(conf)
    except:
        return 0.0
    return max(0.0, min(1.0, conf))