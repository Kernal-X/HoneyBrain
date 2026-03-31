import random
import json
import re
from utils.llm_client import call_llm

# -----------------------------------
# REALISM DATA
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

SENSITIVE_HINTS = [
    "confidential",
    "internal-only",
    "restricted",
    "do not share",
    "privileged access"
]


# -----------------------------------
# HELPERS
# -----------------------------------

def inject_typo(text):
    words = text.split()
    updated = []

    for word in words:
        key = word.lower().strip(".,")
        if key in TYPO_VARIANTS and random.random() < 0.1:
            replacement = random.choice(TYPO_VARIANTS[key])
            if word[0].isupper():
                replacement = replacement.capitalize()
            updated.append(replacement)
        else:
            updated.append(word)

    return " ".join(updated)


def maybe_append_remark(line):
    if random.random() < 0.2:
        return line + "  # " + random.choice(REALISTIC_REMARKS)
    return line


def add_sensitive_hint(line, sensitivity):
    if sensitivity == "high" and random.random() < 0.25:
        return line + f"  # {random.choice(SENSITIVE_HINTS)}"
    return line


def strip_llm_artifacts(text: str) -> str:
    if not text:
        return text

    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"```[a-zA-Z]*", "", text)
    text = text.replace("```", "")

    return text.strip()


# -----------------------------------
# CSV REALISM (SAFE)
# -----------------------------------

def enhance_csv(content, sensitivity):
    lines = content.strip().split("\n")
    cleaned = []

    for i, line in enumerate(lines):
        parts = [p.strip() for p in line.split(",")]
        line = ",".join(parts)

        # do NOT touch header
        if i > 0:
            if random.random() < 0.1:
                line = inject_typo(line)

        cleaned.append(line)

    return "\n".join(cleaned)


# -----------------------------------
# JSON REALISM (SAFE)
# -----------------------------------

def enhance_json(content):
    try:
        data = json.loads(content)
        return json.dumps(data, indent=4)
    except:
        return content


# -----------------------------------
# ENV REALISM
# -----------------------------------

def enhance_env(content, sensitivity):
    lines = content.strip().split("\n")
    updated = []

    for line in lines:
        if "=" in line:
            line = line.strip()

            if sensitivity == "high" and random.random() < 0.2:
                line += "  # rotated recently"

        updated.append(line)

    return "\n".join(updated)


# -----------------------------------
# LOG REALISM (IMPROVED)
# -----------------------------------

def enhance_logs(content, sensitivity):
    lines = content.strip().split("\n")
    updated = []

    for line in lines:
        # Add realistic event mutation
        if "Event=" in line and random.random() < 0.3:
            line = re.sub(
                r"Event=[^ ]+",
                f"Event={random.choice(REALISTIC_LOG_EVENTS)}",
                line
            )

        # Add session or trace IDs
        if random.random() < 0.25:
            line += f" Session={random.randint(1000,9999)}"

        if random.random() < 0.15:
            line += f" TraceID={random.randint(100000,999999)}"

        line = add_sensitive_hint(line, sensitivity)
        updated.append(line)

    return "\n".join(updated)


# -----------------------------------
# TEXT / NOTE REALISM
# -----------------------------------

def enhance_text(content, sensitivity):
    lines = content.strip().split("\n")
    updated = []

    for line in lines:
        if random.random() < 0.4:
            line += " " + random.choice(REALISTIC_NOTE_SUFFIXES)

        if random.random() < 0.15:
            line = inject_typo(line)

        line = add_sensitive_hint(line, sensitivity)

        updated.append(line)

    return "\n".join(updated)


# -----------------------------------
# CREDENTIAL REALISM
# -----------------------------------

def enhance_credentials(content, sensitivity):
    lines = content.strip().split("\n")
    updated = []

    for line in lines:
        if random.random() < 0.25:
            line = maybe_append_remark(line)

        line = add_sensitive_hint(line, sensitivity)

        updated.append(line)

    return "\n".join(updated)


# -----------------------------------
# SQL REALISM (NEW 🔥)
# -----------------------------------

def enhance_sql(content, sensitivity):
    lines = content.strip().split("\n")
    updated = []

    for line in lines:
        if "INSERT INTO" in line.upper() and random.random() < 0.3:
            line += " -- batch insert"

        if "CREATE TABLE" in line.upper() and sensitivity == "high":
            line += " -- critical table"

        updated.append(line)

    return "\n".join(updated)


# -----------------------------------
# OPTIONAL LLM ENHANCEMENT
# -----------------------------------

def enhance_with_llm(content, metadata):
    file_type = metadata.get("file_type", "").lower()
    content_type = metadata.get("content_type", "").lower()

    # avoid fragile structured formats
    if file_type in ["csv", "json", "env"]:
        return content

    prompt = f"""
Improve realism of this enterprise file.

Constraints:
- DO NOT change structure
- DO NOT add/remove rows or fields
- DO NOT explain
- NO markdown

Content:
{content}
"""

    improved = call_llm(prompt, temperature=0.2, max_tokens=1200, mode="generation")

    if not improved:
        return content

    return strip_llm_artifacts(improved)


# -----------------------------------
# MAIN ENTRY
# -----------------------------------

def apply(content, metadata):
    file_type = metadata.get("file_type", "").lower()
    content_type = metadata.get("content_type", "").lower()
    sensitivity = metadata.get("sensitivity", "medium").lower()
    realism_level = metadata.get("realism_level", "medium").lower()

    # Step 1: deterministic realism
    if file_type == "csv":
        content = enhance_csv(content, sensitivity)

    elif file_type == "json":
        content = enhance_json(content)

    elif file_type == "sql":
        content = enhance_sql(content, sensitivity)

    elif file_type == "env":
        content = enhance_env(content, sensitivity)

    elif file_type == "txt":
        if content_type == "credentials":
            content = enhance_credentials(content, sensitivity)
        elif content_type == "logs":
            content = enhance_logs(content, sensitivity)
        elif content_type == "env":
            content = enhance_env(content, sensitivity)
        else:
            content = enhance_text(content, sensitivity)

    elif file_type == "log":
        content = enhance_logs(content, sensitivity)

    else:
        content = enhance_text(content, sensitivity)

    # Step 2: optional LLM realism
    if realism_level == "high" and metadata.get("use_llm_realism", False):
        content = enhance_with_llm(content, metadata)

    return content