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

LOG_ACTIONS = [
    "login success",
    "payroll export initiated",
    "backup completed",
    "finance report downloaded",
    "vendor sync completed",
    "credential validation passed",
    "access policy updated",
    "restricted folder reviewed"
]


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
    except Exception:
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
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59)
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


def random_aws_access_key():
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "AKIA" + "".join(random.choices(chars, k=16))  # total 20 chars


def get_row_count(size):
    if size == "small":
        return random.randint(3, 5)
    elif size == "medium":
        return random.randint(6, 10)
    elif size == "large":
        return random.randint(12, 20)
    return 5


def build_employee_pool(row_count, context):
    """
    Build deterministic unique employee rows for structured artifacts.
    Prevent duplicate IDs and improve realism.
    """
    names = context["employee_names"][:]
    random.shuffle(names)

    rows = []
    for i in range(row_count):
        name = names[i % len(names)]
        department = random.choice(context["departments"])
        role = random.choice(ROLES)
        email = random_email(name, context["email_domains"])

        rows.append({
            "employee_id": f"E{100 + i}",
            "name": name,
            "department": department,
            "email": email,
            "role": role
        })

    return rows


# ----------------------------
# ENV GENERATION
# ----------------------------

def generate_env_file(metadata):
    """
    Generate fake .env / config-style secret file.
    """
    context = load_global_context()

    chosen_project = random.choice(context["project_names"]).lower()
    chosen_employee = random.choice(context["employee_names"]).lower().replace(" ", ".")
    db_user = random.choice(["finance_admin", "svc_backup", "internal_user", "ops_admin"])
    db_pass = random_password()
    jwt_secret = f"jwt_{random.randint(100000,999999)}_{chosen_project}"
    api_key = f"sk_live_{random.randint(10000000,99999999)}"
    aws_key = random_aws_access_key()

    lines = [
        "APP_ENV=production",
        f"APP_NAME={chosen_project}_service",
        f"DB_HOST=10.10.{random.randint(1,20)}.{random.randint(2,250)}",
        "DB_PORT=5432",
        f"DB_NAME={chosen_project}_db",
        f"DB_USER={db_user}",
        f"DB_PASSWORD={db_pass}",
        f"JWT_SECRET={jwt_secret}",
        f"API_KEY={api_key}",
        f"AWS_ACCESS_KEY_ID={aws_key}",
        f"SERVICE_OWNER={chosen_employee}",
        "DEBUG=false"
    ]

    return "\n".join(lines)


# ----------------------------
# CSV GENERATION
# ----------------------------

def generate_csv(schema, metadata):
    """
    Generate schema-safe CSV with unique rows.
    """
    context = load_global_context()
    row_count = get_row_count(metadata.get("size", "medium"))
    employee_pool = build_employee_pool(row_count, context)

    csv_lines = [",".join(schema)]

    for i, person in enumerate(employee_pool):
        row = []

        for col in schema:
            col_lower = col.lower()

            if "employee_id" in col_lower:
                row.append(person["employee_id"])

            elif "name" in col_lower and "vendor" not in col_lower:
                row.append(person["name"])

            elif "vendor_name" in col_lower:
                row.append(f"Vendor_{i+1}")

            elif "department" in col_lower:
                row.append(person["department"])

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
                row.append(person["email"])

            elif "role" in col_lower:
                row.append(person["role"])

            elif "project" in col_lower:
                row.append(random.choice(context["project_names"]))

            elif "timestamp" in col_lower:
                row.append(random_date())

            elif "level" in col_lower:
                row.append(random.choice(LOG_LEVELS))

            elif "message" in col_lower:
                row.append(f"Action completed for {person['name']}")

            else:
                row.append(f"value_{i+1}")

        csv_lines.append(",".join(row))

    return "\n".join(csv_lines)


# ----------------------------
# CREDENTIAL FILE GENERATION
# ----------------------------

def generate_credentials(metadata):
    """
    Generate fake credential-style text file.
    Avoid duplicate usernames within same file.
    """
    context = load_global_context()
    row_count = get_row_count(metadata.get("size", "small"))

    names = context["employee_names"][:]
    random.shuffle(names)
    selected = names[:row_count]

    lines = []
    for name in selected:
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
    row_count = get_row_count(metadata.get("size", "medium"))

    lines = []
    for _ in range(row_count):
        ts = random_date()
        level = random.choice(LOG_LEVELS)
        user = random.choice(context["employee_names"]).lower().replace(" ", ".")
        action = random.choice(LOG_ACTIONS)
        project = random.choice(context["project_names"])

        line = f"[{ts}] [{level}] User={user} Event={action} Project={project}"

        if random.random() < 0.35:
            line += f" Session={random.randint(1000,9999)}"

        lines.append(line)

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
    Generate schema-safe JSON with unique employee IDs.
    """
    context = load_global_context()
    row_count = get_row_count(metadata.get("size", "medium"))
    employee_pool = build_employee_pool(row_count, context)

    data = []

    for i, person in enumerate(employee_pool):
        item = {}

        for col in schema:
            col_lower = col.lower()

            if "employee_id" in col_lower:
                item[col] = person["employee_id"]

            elif "name" in col_lower:
                item[col] = person["name"]

            elif "department" in col_lower:
                item[col] = person["department"]

            elif "salary" in col_lower:
                item[col] = random.randint(45000, 120000)

            elif "email" in col_lower:
                item[col] = person["email"]

            elif "role" in col_lower:
                item[col] = person["role"]

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
    """
    file_type = metadata.get("file_type", "").lower()
    content_type = metadata.get("content_type", "").lower()

    if file_type == "csv":
        return generate_csv(schema, metadata)

    elif file_type == "json":
        return generate_json(schema, metadata)

    elif file_type == "txt":
        if content_type == "credentials":
            return generate_credentials(metadata)
        elif content_type == "logs":
            return generate_logs(metadata)
        elif content_type == "env":
            return generate_env_file(metadata)
        else:
            return generate_text_note(metadata)

    elif file_type == "log":
        return generate_logs(metadata)

    return generate_text_note(metadata)