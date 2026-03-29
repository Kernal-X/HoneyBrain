INTENTS = [
    "credential_bruteforce", "data_exfiltration", "reconnaissance",
    "privilege_escalation", "lateral_movement", "persistence",
    "insider_threat", "benign_activity", "unknown"
]

STAGES = [
    "initial_access", "credential_access", "execution",
    "lateral_movement", "collection", "exfiltration",
    "persistence", "unknown"
]


def sanitize_output(output):
    intent = output.get("intent", "unknown")
    stage = output.get("attack_stage", "unknown")

    if intent not in INTENTS:
        intent = "unknown"

    if stage not in STAGES:
        stage = "unknown"

    try:
        confidence = float(output.get("confidence", 0))
    except:
        confidence = 0.0

    confidence = max(0.0, min(1.0, confidence))

    reasoning = output.get("reasoning", [])
    if not isinstance(reasoning, list):
        reasoning = ["invalid reasoning"]

    return {
        "intent": intent,
        "attack_stage": stage,
        "confidence": confidence,
        "reasoning": reasoning[:2]
    }