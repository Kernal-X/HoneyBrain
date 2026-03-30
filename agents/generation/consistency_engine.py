import json
import random
import re
import csv
import io

# -----------------------------------
# GLOBAL PERSON + ORG PROFILES
# -----------------------------------

PERSON_PROFILES = {}
ORG_PROFILE = {}

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

PROJECTS = [
    "Orion",
    "Atlas",
    "Helios",
    "Nimbus",
    "Phoenix"
]

BANKS = ["HDFC", "ICICI", "SBI", "Axis Bank", "Kotak"]


# -----------------------------------
# HELPERS
# -----------------------------------

def normalize_name(name: str) -> str:
    return str(name).strip().lower()


def build_email(name, domain=None):
    parts = str(name).strip().lower().split()
    if not parts:
        return f"user{random.randint(100,999)}@{random.choice(EMAIL_DOMAINS)}"

    if len(parts) >= 2:
        local = f"{parts[0]}.{parts[1]}"
    else:
        local = parts[0]

    if not domain:
        domain = random.choice(EMAIL_DOMAINS)

    return f"{local}@{domain}"


def build_employee_id(name):
    seed = abs(hash(normalize_name(name))) % 9000 + 1000
    return f"E{seed}"


def build_phone():
    return f"+91-{random.randint(70000,99999)}{random.randint(10000,99999)}"


def build_account_no():
    return str(random.randint(1000000000, 9999999999))


def build_ifsc(bank=None):
    prefixes = {
        "HDFC": "HDFC",
        "ICICI": "ICIC",
        "SBI": "SBIN",
        "Axis Bank": "UTIB",
        "Kotak": "KKBK"
    }
    if not bank:
        bank = random.choice(BANKS)
    prefix = prefixes.get(bank, "BANK")
    return f"{prefix}{random.randint(100000,999999)}"


def get_org_profile():
    """
    Stable fake organization-level identity.
    """
    if not ORG_PROFILE:
        chosen_domain = random.choice(EMAIL_DOMAINS)
        chosen_project = random.choice(PROJECTS)
        ORG_PROFILE.update({
            "email_domain": chosen_domain,
            "primary_project": chosen_project,
            "db_host_prefix": f"10.10.{random.randint(1,20)}",
            "app_name": f"{chosen_project.lower()}_service",
            "bank_name": random.choice(BANKS)
        })

    return ORG_PROFILE


def get_or_create_profile(name):
    """
    Return a stable identity profile for a given person.
    """
    key = normalize_name(name)
    org = get_org_profile()

    if key not in PERSON_PROFILES:
        bank_name = random.choice(BANKS)
        PERSON_PROFILES[key] = {
            "employee_id": build_employee_id(name),
            "department": random.choice(DEPARTMENTS),
            "role": random.choice(ROLES),
            "email": build_email(name, org["email_domain"]),
            "phone": build_phone(),
            "bank_name": bank_name,
            "account_no": build_account_no(),
            "ifsc": build_ifsc(bank_name)
        }

    return PERSON_PROFILES[key]


def normalize_field_name(field):
    return str(field).strip().lower()


# -----------------------------------
# VALUE ENRICHMENT
# -----------------------------------

def enrich_row_with_profile(row):
    """
    Apply stable person/org consistency to a structured row dict.
    """
    org = get_org_profile()

    possible_name_keys = ["name", "full_name", "employee_name", "owner_name"]
    name = None

    for key in possible_name_keys:
        if key in row and str(row.get(key, "")).strip():
            name = row[key]
            break

    if not name:
        return row

    profile = get_or_create_profile(name)

    for key in list(row.keys()):
        key_lower = normalize_field_name(key)

        if key_lower in ["employee_id", "emp_id", "staff_id"]:
            row[key] = profile["employee_id"]

        elif key_lower in ["name", "full_name", "employee_name", "owner_name"]:
            row[key] = name

        elif "department" in key_lower:
            row[key] = profile["department"]

        elif "email" in key_lower:
            row[key] = profile["email"]

        elif key_lower in ["role", "user_role", "access_role"]:
            row[key] = profile["role"]

        elif "phone" in key_lower or "mobile" in key_lower:
            row[key] = profile["phone"]

        elif "account_no" in key_lower or "account_number" in key_lower or "bank_account" in key_lower:
            row[key] = profile["account_no"]

        elif "bank_name" in key_lower:
            row[key] = profile["bank_name"]

        elif "ifsc" in key_lower:
            row[key] = profile["ifsc"]

        elif "project" in key_lower:
            row[key] = org["primary_project"]

        elif key_lower in ["service_owner", "owner", "owner_email"]:
            row[key] = profile["email"]

    return row


# -----------------------------------
# CSV CONSISTENCY
# -----------------------------------

def apply_csv_consistency(content):
    try:
        reader = list(csv.reader(io.StringIO(content)))
        if len(reader) < 2:
            return content

        headers = [h.strip() for h in reader[0]]
        rows = []

        for raw_row in reader[1:]:
            row = dict(zip(headers, raw_row))
            row = enrich_row_with_profile(row)
            rows.append(row)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)

        for row in rows:
            writer.writerow([row.get(h, "") for h in headers])

        return output.getvalue().strip()

    except Exception:
        return content


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
            enrich_row_with_profile(item)

        return json.dumps(data, indent=4)

    except Exception:
        return content


# -----------------------------------
# SQL CONSISTENCY
# -----------------------------------

def apply_sql_consistency(content):
    """
    Lightweight SQL consistency pass.
    Keeps org-level identifiers stable where possible.
    """
    org = get_org_profile()
    updated = content

    # stabilize app/service names if generic placeholders exist
    updated = re.sub(r"\binternal_service\b", org["app_name"], updated, flags=re.IGNORECASE)

    # stabilize DB hosts like 10.10.x.y pattern if present
    updated = re.sub(
        r"\b10\.10\.\d{1,2}\.\d{1,3}\b",
        f"{org['db_host_prefix']}.{random.randint(2,250)}",
        updated
    )

    return updated


# -----------------------------------
# ENV / CONFIG CONSISTENCY
# -----------------------------------

def apply_env_consistency(content):
    org = get_org_profile()
    lines = []

    for line in content.splitlines():
        stripped = line.strip()

        if stripped.startswith("APP_NAME="):
            lines.append(f"APP_NAME={org['app_name']}")

        elif stripped.startswith("DB_HOST="):
            lines.append(f"DB_HOST={org['db_host_prefix']}.{random.randint(2,250)}")

        elif stripped.startswith("SERVICE_OWNER="):
            sample_name = random.choice([
                "Aarav Singh", "Neha Verma", "Rahul Kapoor", "Priya Shah"
            ])
            profile = get_or_create_profile(sample_name)
            lines.append(f"SERVICE_OWNER={profile['email'].split('@')[0]}")

        else:
            lines.append(line)

    return "\n".join(lines)


# -----------------------------------
# TEXT / LOG CONSISTENCY
# -----------------------------------

def apply_text_consistency(content):
    """
    Light text consistency:
    - stabilize project names
    - stabilize email domains
    """
    org = get_org_profile()
    updated = content

    # replace mixed domains with stable org domain
    updated = re.sub(
        r"\b([a-z]+\.[a-z]+)@(internal\.corp|corp\.local|mail\.corp\.local)\b",
        rf"\1@{org['email_domain']}",
        updated,
        flags=re.IGNORECASE
    )

    # normalize known project names into stable org project sometimes
    for project in PROJECTS:
        if project != org["primary_project"] and random.random() < 0.4:
            updated = updated.replace(project, org["primary_project"])

    return updated


# -----------------------------------
# MAIN ENTRY
# -----------------------------------

def apply(content, metadata):
    file_type = str(metadata.get("file_type", "")).lower()

    if file_type == "csv":
        return apply_csv_consistency(content)

    elif file_type == "json":
        return apply_json_consistency(content)

    elif file_type == "sql":
        return apply_sql_consistency(content)

    elif file_type == "env":
        return apply_env_consistency(content)

    elif file_type in ["txt", "log"]:
        return apply_text_consistency(content)

    return content