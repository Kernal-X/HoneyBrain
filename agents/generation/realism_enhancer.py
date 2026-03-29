import random
import json

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
        if key in TYPO_VARIANTS and random.random() < 0.15:
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
    if random.random() < 0.35:
        return line + "  # " + random.choice(REALISTIC_REMARKS)
    return line


# -----------------------------------
# CSV REALISM
# -----------------------------------

def enhance_csv(content, metadata):
    """
    Add realistic columns / comments where useful without breaking structure.
    """
    lines = content.strip().split("\n")
    if len(lines) < 2:
        return content

    headers = lines[0].split(",")
    rows = [line.split(",") for line in lines[1:]]

    # Optional remarks column
    if metadata.get("realism_level", "medium") == "high":
        if "remarks" not in [h.lower() for h in headers]:
            headers.append("remarks")

            for row in rows:
                row.append(random.choice(REALISTIC_REMARKS))

    updated_lines = [",".join(headers)]
    for row in rows:
        updated_lines.append(",".join(row))

    return "\n".join(updated_lines)


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
        if random.random() < 0.5:
            line += " " + random.choice(REALISTIC_NOTE_SUFFIXES)

        if random.random() < 0.2:
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
        if random.random() < 0.25:
            line = maybe_append_remark(line)
        updated.append(line)

    return "\n".join(updated)


# -----------------------------------
# JSON REALISM
# -----------------------------------

def enhance_json(content, metadata):
    """
    Add optional natural-text fields to JSON structures.
    """
    try:
        data = json.loads(content)
        if not isinstance(data, list):
            return content

        for item in data:
            if not isinstance(item, dict):
                continue

            if metadata.get("realism_level", "medium") == "high":
                if "remarks" not in item:
                    item["remarks"] = random.choice(REALISTIC_REMARKS)

        return json.dumps(data, indent=4)

    except:
        return content


# -----------------------------------
# OPTIONAL LLM ENHANCEMENT HOOK
# -----------------------------------

def enhance_with_llm(content, metadata):
    """
    Placeholder for future LLM-based realism enhancement.

    Intended use:
    - polishing internal notes
    - making audit comments more natural
    - improving memo-style documents

    IMPORTANT:
    This should never break schema or structure.
    """
    return content


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
        content = enhance_csv(content, metadata)

    elif file_type == "json":
        content = enhance_json(content, metadata)

    elif file_type == "txt":
        if content_type == "credentials":
            content = enhance_credentials(content)
        elif content_type == "logs":
            content = enhance_logs(content)
        else:
            content = enhance_text(content)

    elif file_type == "log":
        content = enhance_logs(content)

    else:
        content = enhance_text(content)

    # Step 2: Optional LLM realism (only if explicitly high)
    if realism_level == "high" and metadata.get("use_llm_realism", False):
        content = enhance_with_llm(content, metadata)

    return content