import json
import random

# -----------------------------------
# GLOBAL PERSON PROFILES
# -----------------------------------

PERSON_PROFILES = {}

EMAIL_DOMAINS = [
    "internal.corp",
    "corp.local",
    "mail.corp.local"
]

DEPARTMENTS = [
    "Finance",
    "HR",
    "Engineering",
    "Operations",
    "Compliance",
    "Security",
    "Admin"
]

ROLES = [
    "admin",
    "analyst",
    "user",
    "finance_admin",
    "svc_backup"
]


# -----------------------------------
# HELPERS
# -----------------------------------

def normalize_name(name: str) -> str:
    return name.strip().lower()


def build_email(name, domain=None):
    parts = name.lower().split()
    if len(parts) >= 2:
        local = f"{parts[0]}.{parts[1]}"
    else:
        local = parts[0]

    if not domain:
        domain = random.choice(EMAIL_DOMAINS)

    return f"{local}@{domain}"


def get_or_create_profile(name):
    """
    Return a stable identity profile for a given person.
    """
    key = normalize_name(name)

    if key not in PERSON_PROFILES:
        PERSON_PROFILES[key] = {
            "department": random.choice(DEPARTMENTS),
            "role": random.choice(ROLES),
            "email": build_email(name)
        }

    return PERSON_PROFILES[key]


# -----------------------------------
# CSV CONSISTENCY
# -----------------------------------

def apply_csv_consistency(content):
    lines = content.strip().split("\n")
    if len(lines) < 2:
        return content

    headers = [h.strip() for h in lines[0].split(",")]
    rows = []

    for line in lines[1:]:
        parts = [p.strip() for p in line.split(",")]
        row = dict(zip(headers, parts))

        name = row.get("name")
        if name:
            profile = get_or_create_profile(name)

            if "department" in row:
                row["department"] = profile["department"]
            if "email" in row:
                row["email"] = profile["email"]
            if "role" in row:
                row["role"] = profile["role"]

        rows.append(row)

    output = [",".join(headers)]
    for row in rows:
        output.append(",".join(row.get(h, "") for h in headers))

    return "\n".join(output)


# -----------------------------------
# JSON CONSISTENCY
# -----------------------------------

def apply_json_consistency(content):
    try:
        data = json.loads(content)
        if not isinstance(data, list):
            return content

        for item in data:
            if not isinstance(item, dict):
                continue

            name = item.get("name")
            if name:
                profile = get_or_create_profile(name)

                if "department" in item:
                    item["department"] = profile["department"]
                if "email" in item:
                    item["email"] = profile["email"]
                if "role" in item:
                    item["role"] = profile["role"]

        return json.dumps(data, indent=4)

    except Exception:
        return content


# -----------------------------------
# TEXT CONSISTENCY
# -----------------------------------

def apply_text_consistency(content):
    """
    Placeholder for future note/log/person consistency.
    """
    return content


# -----------------------------------
# MAIN ENTRY
# -----------------------------------

def apply(content, metadata):
    file_type = metadata.get("file_type", "").lower()

    if file_type == "csv":
        return apply_csv_consistency(content)

    elif file_type == "json":
        return apply_json_consistency(content)

    elif file_type in ["txt", "log"]:
        return apply_text_consistency(content)

    return content