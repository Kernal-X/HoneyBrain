import os

from dotenv import load_dotenv
from groq import Groq
from openai import OpenAI

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


def call_openai_strategy_llm(prompt: str, model: str = "gpt-4o-mini") -> str:
    """
    OpenAI call for Strategy Agent — strict JSON object responses.
    Raises on missing key or API errors (caller handles fallback).
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You emit only one JSON object per request. No markdown, no explanations.",
            },
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.15,
        max_tokens=4096,
    )
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("empty OpenAI response")
    return content