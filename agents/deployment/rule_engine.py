# agents/deployment/rule_engine.py

def build_interception_rules(decoy_registry):
    """
    Build interception rules based on decoy metadata
    """

    rules = {}

    for path, metadata in decoy_registry.items():

        sensitivity = metadata.get("sensitivity", "medium")
        realism = metadata.get("realism", "medium")

        # 🔴 High sensitivity → aggressive deception
        if sensitivity == "high":
            rules[path] = {
                "risk_threshold": 0.5,
                "deception_mode": "full"
            }

        # 🟡 Medium sensitivity → balanced
        elif sensitivity == "medium":
            rules[path] = {
                "risk_threshold": 0.7,
                "deception_mode": "partial"
            }

        # 🟢 Low sensitivity → mostly real
        else:
            rules[path] = {
                "risk_threshold": 0.85,
                "deception_mode": "none"
            }

        # 🔥 Optional tweak: realism boost
        if realism == "high":
            rules[path]["risk_threshold"] -= 0.1  # lie slightly earlier

    return rules