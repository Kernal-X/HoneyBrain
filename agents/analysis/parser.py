import json
import re

def parse_response(response):
    try:
        # remove markdown ```json blocks if present
        cleaned = re.sub(r"```json|```", "", response).strip()

        # extract JSON object using regex
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)

        if match:
            return json.loads(match.group())
        else:
            raise ValueError("No JSON found")

    except Exception as e:
        print("Parse Error:", e)
        return {
            "attack_stage": "unknown",
            "intent": "unknown",
            "confidence": 0.0,
            "reasoning": ["failed to parse response"]
        }