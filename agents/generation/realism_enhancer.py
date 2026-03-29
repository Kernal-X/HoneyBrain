import random
import json
import re
from utils.llm_client import call_llm

# -----------------------------------
# LIGHTWEIGHT REALISM TEMPLATES
# -----------------------------------

REALISTIC_REMARKS = [
    "Pending final approval from finance lead",
    "Reviewed during monthly reconciliation cycle",
    "Requires secondary verification before release",
    "Shared with internal audit for review",
    "Hold until vendor confirmation is received",
    "Marked for payroll review in next cycle",
    "Validated against archived records",
    "Escalated due to mismatch in supporting documents"
]

REALISTIC_NOTE_SUFFIXES = [
    "Need to revisit before external review.",
    "Keep internal until final sign-off.",
    "Do not circulate outside department.",
    "Waiting for approval from operations.",
    "To be reviewed again next reporting cycle.",
    "Pending confirmation from admin side."
]

REALISTIC_LOG_EVENTS = [
    "access validation completed",
    "archive sync initiated",
    "privileged export triggered",
    "backup policy check completed",
    "document access reviewed",
    "restricted folder mapping updated"
]

TYPO_VARIANTS = {
    "approved": ["approved", "aproved"],
    "pending": ["pending", "pendng"],
    "review": ["review", "reivew"],
    "internal": ["internal", "internl"]
}


# -----------------------------------
# HELPERS
# -----------------------------------

def inject_typo(text):
    """
    Introduce small human-like imperfections occasionally.
    """
    words = text.split()
    updated = []

    for word in words:
        key = word.lower().strip(".,")
        if key in TYPO_VARIANTS and random.random() < 0.12:
            replacement = random.choice(TYPO_VARIANTS[key])
            if word[0].isupper():
                replacement = replacement.capitalize()
            updated.append(replacement)
        else:
            updated.append(word)

    return " ".join(updated)


def maybe_append_remark(line):
    """
    Add optional realistic note/comment at end of a line.
    """
    if random.random() < 0.25:
        return line + "  # " + random.choice(REALISTIC_REMARKS)
    return line


def strip_llm_artifacts(text: str) -> str:
    """
    Remove reasoning / markdown / formatting junk from LLM output.
    """
    if not text:
        return text

    # Remove <think>...</think>
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)

    # Remove markdown fences
    text = re.sub(r"```[a-zA-Z]*", "", text)
    text = text.replace("```", "")

    return text.strip()


# -----------------------------------
# CSV REALISM (SAFE)
# -----------------------------------

def enhance_csv(content):
    """
    Keep CSV realism safe.
    Do NOT add/remove columns.
    Only lightly normalize spacing if needed.
    """
    lines = content.strip().split("\n")
    cleaned = []

    for line in lines:
        parts = [p.strip() for p in line.split(",")]
        cleaned.append(",".join(parts))

    return "\n".join(cleaned)


# -----------------------------------
# ENV REALISM (SAFE)
# -----------------------------------

def enhance_env(content):
    """
    Preserve exact .env structure.
    Do NOT add/remove keys here.
    """
    lines = content.strip().split("\n")
    cleaned = []

    for line in lines:
        cleaned.append(line.strip())

    return "\n".join(cleaned)


# -----------------------------------
# LOG REALISM
# -----------------------------------

def enhance_logs(content):
    """
    Add operationally believable noise to log-style files.
    """
    lines = content.strip().split("\n")
    updated = []

    for line in lines:
        if random.random() < 0.3 and "Event=" in line:
            line = line.replace("Event=", f"Event={random.choice(REALISTIC_LOG_EVENTS)} | ")

        if random.random() < 0.2:
            line += f" Session={random.randint(1000,9999)}"

        updated.append(line)

    return "\n".join(updated)


# -----------------------------------
# TEXT / NOTE REALISM
# -----------------------------------

def enhance_text(content):
    """
    Make internal note / text artifacts feel less templated.
    """
    lines = content.strip().split("\n")
    updated = []

    for line in lines:
        if random.random() < 0.45:
            line += " " + random.choice(REALISTIC_NOTE_SUFFIXES)

        if random.random() < 0.15:
            line = inject_typo(line)

        updated.append(line)

    return "\n".join(updated)


# -----------------------------------
# CREDENTIAL FILE REALISM
# -----------------------------------

def enhance_credentials(content):
    """
    Add slight realism to credentials file formatting.
    """
    lines = content.strip().split("\n")
    updated = []

    for line in lines:
        if random.random() < 0.2:
            line = maybe_append_remark(line)
        updated.append(line)

    return "\n".join(updated)


# -----------------------------------
# JSON REALISM (SAFE)
# -----------------------------------

def enhance_json(content):
    """
    Preserve JSON schema strictly.
    No extra keys added.
    """
    try:
        data = json.loads(content)
        return json.dumps(data, indent=4)
    except:
        return content


# -----------------------------------
# OPTIONAL LLM ENHANCEMENT HOOK
# -----------------------------------

def enhance_with_llm(content, metadata):
    """
    LLM should only POLISH realism.
    It should NOT change the structure drastically.
    Only use for semi-unstructured text-like files.
    """
    file_type = metadata.get("file_type", "").lower()
    content_type = metadata.get("content_type", "").lower()

    # SAFETY: do not use LLM on fragile structured files
    if file_type in ["csv", "json", "env"]:
        return content

    if file_type == "txt" and content_type == "env":
        return content

    prompt = f"""
You are improving the realism of a deceptive enterprise artifact for a cybersecurity honeypot.

File type: {file_type}
Content type: {content_type}

Important constraints:
- Preserve exact file structure
- Do NOT remove keys, rows, or fields
- Do NOT add new fields or records
- Do NOT change file format
- Do NOT explain
- Do NOT add markdown
- Do NOT include <think> or reasoning
- Return ONLY the improved file content

Original content:
----------------
{content}
----------------
"""

    improved = call_llm(prompt, temperature=0.2, max_tokens=1200,mode="generation")

    if not improved:
        return content

    return improved.strip()


# -----------------------------------
# MAIN ENTRY FUNCTION
# -----------------------------------

def apply(content, metadata):
    """
    Main realism enhancement entry point.
    Applies lightweight realism upgrades depending on file type.
    """
    file_type = metadata.get("file_type", "").lower()
    content_type = metadata.get("content_type", "").lower()
    realism_level = metadata.get("realism_level", "medium").lower()

    # Step 1: Lightweight deterministic realism
    if file_type == "csv":
        content = enhance_csv(content)

    elif file_type == "json":
        content = enhance_json(content)

    elif file_type == "txt":
        if content_type == "credentials":
            content = enhance_credentials(content)
        elif content_type == "logs":
            content = enhance_logs(content)
        elif content_type == "env":
            content = enhance_env(content)
        else:
            content = enhance_text(content)

    elif file_type == "log":
        content = enhance_logs(content)

    else:
        content = enhance_text(content)

    # Step 2: Optional LLM realism (ONLY for safe text-like artifacts)
    if realism_level == "high" and metadata.get("use_llm_realism", False):
        content = enhance_with_llm(content, metadata)

    return content