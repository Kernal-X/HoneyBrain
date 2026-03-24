def build_prompt(context):
    return f"""
You are a cybersecurity analysis agent.

Risk Score: {context['risk_score']}

Signals:
{context['signals']}

Recent Events:
{context['recent_events']}

Tasks:
1. Identify attack_stage
2. Identify intent (choose from: credential_bruteforce, data_exfiltration, reconnaissance, privilege_escalation)
3. Give confidence (0 to 1)
4. Provide reasoning

Rules:
- Be precise
- Think step-by-step
- Return ONLY JSON

IMPORTANT:
- Output ONLY valid JSON
- Do NOT include explanations
- Do NOT include markdown (no ```json or ```)

Format:
{{
  "attack_stage": "...",
  "intent": "...",
  "confidence": 0.0,
  "reasoning": ["...", "..."]
}}
"""