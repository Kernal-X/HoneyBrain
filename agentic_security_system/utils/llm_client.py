from groq import Groq
import os
from dotenv import load_dotenv
load_dotenv()

def fallback_response():
    return """
    {
      "attack_stage": "unknown",
      "intent": "unknown",
      "confidence": 0.0,
      "reasoning": ["LLM unavailable or failed"]
    }
    """

def call_llm(prompt):
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        print("⚠️ GROQ_API_KEY not set, using fallback")
        return fallback_response()

    client = Groq(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model="qwen/qwen3-32b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return response.choices[0].message.content

    except Exception as e:
        print("Groq Error:", e)
        return fallback_response()