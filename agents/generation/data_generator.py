import random
import json
from datetime import datetime, timedelta
import os

# ----------------------------
# GLOBAL DATA (fallback values)
# ----------------------------

EMPLOYEE_NAMES = [
    "Aarav Singh", "Neha Verma", "Rohan Mehta",
    "Priya Shah", "Karan Joshi", "Ananya Rao",
    "Rahul Kapoor", "Ishita Malhotra"
]

DEPARTMENTS = [
    "Finance", "HR", "Engineering", "Operations",
    "Admin", "Security", "Compliance"
]

BANKS = ["HDFC", "ICICI", "SBI", "Axis Bank", "Kotak"]

ROLES = ["admin", "user", "finance_admin", "svc_backup", "analyst"]

PROJECTS = ["Orion", "Atlas", "Helios", "Nimbus", "Phoenix"]

EMAIL_DOMAINS = ["corp.local", "internal.corp", "mail.corp.local"]

LOG_LEVELS = ["INFO", "WARN", "ERROR", "DEBUG"]


# ----------------------------
# OPTIONAL GLOBAL CONTEXT LOADER
# ----------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GLOBAL_CONTEXT_PATH = os.path.join(BASE_DIR, "context", "global_context.json")


def load_global_context():
    """
    Load reusable fake organization context if available.
    Falls back to built-in values if file missing.
    """
    if not os.path.exists(GLOBAL_CONTEXT_PATH):
        return {
            "employee_names": EMPLOYEE_NAMES,
            "departments": DEPARTMENTS,
            "email_domains": EMAIL_DOMAINS,
            "project_names": PROJECTS
        }

    try:
        with open(GLOBAL_CONTEXT_PATH, "r") as f:
            data = json.load(f)

        return {
            "employee_names": data.get("employee_names", EMPLOYEE_NAMES),
            "departments": data.get("departments", DEPARTMENTS),
            "email_domains": data.get("email_domains", EMAIL_DOMAINS),
            "project_names": data.get("project_names", PROJECTS)
        }
    except:
        return {
            "employee_names": EMPLOYEE_NAMES,
            "departments": DEPARTMENTS,
            "email_domains": EMAIL_DOMAINS,
            "project_names": PROJECTS
        }


# ----------------------------
# HELPERS
# ----------------------------

def random_date():
    days_ago = random.randint(1, 180)
    dt = datetime.now() - timedelta(
        days=days_ago,
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59)
    )
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def random_email(name, domains):
    username = name.lower().replace(" ", ".")
    return f"{username}@{random.choice(domains)}"


def random_password():
    base = random.choice(["Admin", "Secure", "Backup", "FinOps", "Access"])
    return f"{base}@{random.randint(100,999)}"


def random_ifsc():
    return f"{random.choice(['HDFC','ICIC','SBIN','UTIB'])}{random.randint(100000,999999)}"


def get_row_count(size):
    if size == "small":
        return random.randint(3, 5)
    elif size == "medium":
        return random.randint(6, 10)
    elif size == "large":
        return random.randint(12, 20)
    return 5


# ----------------------------
# CSV GENERATION
# ----------------------------

def generate_csv(schema, metadata):
    """
    Generate base structured CSV content from schema.
    """
    context = load_global_context()
    row_count = get_row_count(metadata.get("size", "medium"))

    rows = []
    headers = schema

    for i in range(row_count):
        row = []

        chosen_name = random.choice(context["employee_names"])
        chosen_department = random.choice(context["departments"])

        for col in schema:
            col_lower = col.lower()

            if "employee_id" in col_lower:
                row.append(f"E{100+i}")

            elif "name" in col_lower and "vendor" not in col_lower:
                row.append(chosen_name)

            elif "vendor_name" in col_lower:
                row.append(f"Vendor_{i+1}")

            elif "department" in col_lower:
                row.append(chosen_department)

            elif "salary" in col_lower:
                row.append(str(random.randint(45000, 120000)))

            elif "account_no" in col_lower:
                row.append(str(random.randint(10000000, 99999999)))

            elif "bank_name" in col_lower:
                row.append(random.choice(BANKS))

            elif "ifsc" in col_lower:
                row.append(random_ifsc())

            elif "payment_status" in col_lower:
                row.append(random.choice(["Paid", "Pending", "On Hold"]))

            elif "email" in col_lower:
                row.append(random_email(chosen_name, context["email_domains"]))

            elif "role" in col_lower:
                row.append(random.choice(ROLES))

            elif "project" in col_lower:
                row.append(random.choice(context["project_names"]))

            elif "timestamp" in col_lower:
                row.append(random_date())

            elif "level" in col_lower:
                row.append(random.choice(LOG_LEVELS))

            elif "message" in col_lower:
                row.append(f"Action completed for {chosen_name}")

            else:
                row.append(f"value_{i+1}")

        rows.append(row)

    # Build CSV string
    csv_lines = [",".join(headers)]
    for row in rows:
        csv_lines.append(",".join(row))

    return "\n".join(csv_lines)


# ----------------------------
# CREDENTIAL FILE GENERATION
# ----------------------------

def generate_credentials(metadata):
    """
    Generate fake credential-style text file.
    """
    context = load_global_context()
    lines = []

    row_count = get_row_count(metadata.get("size", "small"))

    for _ in range(row_count):
        name = random.choice(context["employee_names"])
        username = name.lower().replace(" ", ".")
        role = random.choice(ROLES)
        password = random_password()

        lines.append(f"{username} : {password} ({role})")

    return "\n".join(lines)


# ----------------------------
# LOG FILE GENERATION
# ----------------------------

def generate_logs(metadata):
    """
    Generate fake log-style file.
    """
    context = load_global_context()
    lines = []

    row_count = get_row_count(metadata.get("size", "medium"))

    for _ in range(row_count):
        ts = random_date()
        level = random.choice(LOG_LEVELS)
        user = random.choice(context["employee_names"]).lower().replace(" ", ".")
        action = random.choice([
            "login success",
            "payroll export initiated",
            "backup completed",
            "finance report downloaded",
            "vendor sync completed",
            "credential validation passed"
        ])
        lines.append(f"[{ts}] [{level}] User={user} Event={action}")

    return "\n".join(lines)


# ----------------------------
# NOTE / TXT FILE GENERATION
# ----------------------------

def generate_text_note(metadata):
    """
    Generate fake internal note / operational text.
    """
    context = load_global_context()

    notes = [
        f"Quarterly review pending for project {random.choice(context['project_names'])}.",
        "Vendor reconciliation sheet needs update before external audit.",
        "Payroll review flagged 2 pending approvals from Finance.",
        "Do not share contractor list outside internal mail.",
        "Backup credentials rotated last cycle. Confirm access with admin team.",
        f"Escalate budget variance issue to {random.choice(context['employee_names'])}."
    ]

    return "\n".join(random.sample(notes, min(4, len(notes))))


# ----------------------------
# JSON GENERATION
# ----------------------------

def generate_json(schema, metadata):
    """
    Generate fake JSON-like structured content.
    """
    context = load_global_context()
    row_count = get_row_count(metadata.get("size", "small"))

    data = []

    for i in range(row_count):
        item = {}
        chosen_name = random.choice(context["employee_names"])
        chosen_department = random.choice(context["departments"])

        for col in schema:
            col_lower = col.lower()

            if "employee_id" in col_lower:
                item[col] = f"E{100+i}"
            elif "name" in col_lower:
                item[col] = chosen_name
            elif "department" in col_lower:
                item[col] = chosen_department
            elif "salary" in col_lower:
                item[col] = random.randint(45000, 120000)
            elif "email" in col_lower:
                item[col] = random_email(chosen_name, context["email_domains"])
            elif "role" in col_lower:
                item[col] = random.choice(ROLES)
            elif "timestamp" in col_lower:
                item[col] = random_date()
            else:
                item[col] = f"value_{i+1}"

        data.append(item)

    return json.dumps(data, indent=4)


# ----------------------------
# MAIN ENTRY FUNCTION
# ----------------------------

def generate(path, metadata, schema):
    """
    Main entry point for Generation Agent.
    Decides how to generate base content depending on file type.
    """
    file_type = metadata.get("file_type", "").lower()
    content_type = metadata.get("content_type", "").lower()

    # CSV-like files
    if file_type == "csv":
        return generate_csv(schema, metadata)

    # JSON-like files
    elif file_type == "json":
        return generate_json(schema, metadata)

    # TXT files with specific meaning
    elif file_type == "txt":
        if content_type == "credentials":
            return generate_credentials(metadata)
        elif content_type == "logs":
            return generate_logs(metadata)
        else:
            return generate_text_note(metadata)

    # LOG files
    elif file_type == "log":
        return generate_logs(metadata)

    # fallback
    return generate_text_note(metadata)