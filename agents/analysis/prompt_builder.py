def build_prompt(risk_score, formatted_events):
    return f"""
You are a cybersecurity analysis agent.

You are given system behavior events with detailed features and an overall risk score.

Your job:
1. Identify attacker intent
2. Identify attack stage
3. Provide confidence (0-1)
4. Provide reasoning

Important:
- Use patterns across multiple events
- Consider process behavior (CPU, memory, parent process)
- Do NOT classify normal system processes as attacks
- Behavioral anomaly alone does NOT mean attack

Allowed intents:
credential_bruteforce, data_exfiltration, reconnaissance,
privilege_escalation, lateral_movement, persistence,
insider_threat, benign_activity, unknown

Allowed attack stages:
initial_access, credential_access, execution,
lateral_movement, collection, exfiltration,
persistence, unknown

Risk Score: {risk_score}

Events:
{formatted_events}

Output JSON ONLY:
{{
  "intent": "...",
  "attack_stage": "...",
  "confidence": 0.0,
  "reasoning": [
    "Evidence-based justification for the chosen INTENT, mapping specific event attributes (e.g., process lineage, network destination) to the adversary's likely goal.",
    "Structural justification for the chosen ATTACK_STAGE, explaining where these actions fall in the kill-chain relative to the provided Risk Score.",
    "Counter-argument analysis: Explain why this behavior is NOT a benign system process or a different attack stage (e.g., why this is 'Lateral Movement' and not just 'Discovery').",
    "Analysis of anomalies: Detailed breakdown of how CPU/Memory or Parent-Child process relationships influenced the final classification."
  ]
}}
"""