import json
import re
import ast

def parse_response(response):
    try:
        # ✅ Case 1: already a dict
        if isinstance(response, dict):
            return response

        # ✅ Case 2: must be string from here
        if not isinstance(response, str):
            raise ValueError("Unsupported response type")

        cleaned = re.sub(r"```json|```", "", response).strip()

        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise ValueError("No JSON found")

        content = match.group()

        # ✅ Try strict JSON first
        try:
            return json.loads(content)
        except:
            pass

        # ✅ Fallback: Python-style dict (LLM nonsense)
        try:
            return ast.literal_eval(content)
        except:
            pass

        raise ValueError("Parsing failed")

    except Exception as e:
        print("Parse Error:", e)
        return {
            "intent": "unknown",
            "attack_stage": "unknown",
            "confidence": 0.0,
            "reasoning": ["failed to parse"]
        }


def normalize_output(data):
    return {
        "intent": data.get("intent", "unknown"),
        "attack_stage": data.get("attack_stage", "unknown"),
        "confidence": float(data.get("confidence", 0.0)),
        "reasoning": data.get("reasoning", [])
    }