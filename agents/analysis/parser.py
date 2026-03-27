import json
import re

def parse_response(response):
    try:
        cleaned = re.sub(r"```json|```", "", response).strip()
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)

        if match:
            return json.loads(match.group())

        raise ValueError("No JSON found")

    except Exception as e:
        print("Parse Error:", e)
        return {
            "intent": "unknown",
            "attack_stage": "unknown",
            "confidence": 0.0,
            "reasoning": ["failed to parse"]
        }