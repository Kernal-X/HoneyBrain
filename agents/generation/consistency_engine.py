import json
import os
import random

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GLOBAL_CONTEXT_PATH = os.path.join(BASE_DIR, "context", "global_context.json")


# ----------------------------
# LOAD GLOBAL CONTEXT
# ----------------------------

def load_global_context():
    """
    Loads fake organization context used to maintain consistency
    across generated decoy files.
    """
    if not os.path.exists(GLOBAL_CONTEXT_PATH):
        return {
            "employee_names": [
                "Aarav Singh", "Neha Verma", "Rohan Mehta",
                "Priya Shah", "Karan Joshi"
            ],
            "departments": ["Finance", "HR", "Engineering", "Operations"],
            "email_domains": ["corp.local"],
            "project_names": ["Orion", "Atlas", "Helios"]
        }

    try:
        with open(GLOBAL_CONTEXT_PATH, "r") as f:
            return json.load(f)
    except:
        return {
            "employee_names": [
                "Aarav Singh", "Neha Verma", "Rohan Mehta",
                "Priya Shah", "Karan Joshi"
            ],
            "departments": ["Finance", "HR", "Engineering", "Operations"],
            "email_domains": ["corp.local"],
            "project_names": ["Orion", "Atlas", "Helios"]
        }


# ----------------------------
# HELPERS
# ----------------------------

def name_to_username(name):
    return name.lower().replace(" ", ".")


def name_to_email(name, domains):
    return f"{name_to_username(name)}@{random.choice(domains)}"


# ----------------------------
# CSV CONSISTENCY
# ----------------------------

def apply_csv_consistency(content, metadata, context):
    """
    Ensure CSV content reuses consistent fake organization entities.
    """
    lines = content.strip().split("\n")
    if len(lines) < 2:
        return content

    headers = lines[0].split(",")
    data_lines = lines[1:]

    updated_rows = []

    for row in data_lines:
        values = row.split(",")
        row_map = dict(zip(headers, values))

        # Choose a consistent fake employee
        chosen_name = random.choice(context["employee_names"])
        chosen_department = random.choice(context["departments"])
        chosen_email = name_to_email(chosen_name, context["email_domains"])
        chosen_project = random.choice(context["project_names"])

        for header in headers:
            h = header.lower()

            if "name" in h and "vendor" not in h:
                row_map[header] = chosen_name

            elif "department" in h:
                row_map[header] = chosen_department

            elif "email" in h:
                row_map[header] = chosen_email

            elif "username" in h:
                row_map[header] = name_to_username(chosen_name)

            elif "project" in h:
                row_map[header] = chosen_project

        updated_rows.append(",".join([row_map[h] for h in headers]))

    return "\n".join([",".join(headers)] + updated_rows)


# ----------------------------
# CREDENTIAL FILE CONSISTENCY
# ----------------------------

def apply_credentials_consistency(content, context):
    """
    Ensure credentials use known employee identities.
    """
    lines = content.strip().split("\n")
    updated = []

    for line in lines:
        chosen_name = random.choice(context["employee_names"])
        username = name_to_username(chosen_name)

        # Keep existing password/role part if possible
        if ":" in line:
            rest = line.split(":", 1)[1].strip()
            updated.append(f"{username} : {rest}")
        else:
            updated.append(f"{username} : Secure@123 (user)")

    return "\n".join(updated)


# ----------------------------
# LOG FILE CONSISTENCY
# ----------------------------

def apply_log_consistency(content, context):
    """
    Ensure logs reference consistent usernames and projects.
    """
    lines = content.strip().split("\n")
    updated = []

    for line in lines:
        chosen_name = random.choice(context["employee_names"])
        username = name_to_username(chosen_name)
        project = random.choice(context["project_names"])

        line = line.replace("User=unknown", f"User={username}")

        # If log already has "User=" replace user segment roughly
        if "User=" in line:
            parts = line.split("User=")
            prefix = parts[0]
            suffix = parts[1]

            if " " in suffix:
                suffix_parts = suffix.split(" ", 1)
                suffix = f"{username} {suffix_parts[1]}"
            else:
                suffix = username

            line = prefix + "User=" + suffix

        # Optional project injection
        if "Event=" in line and "Project=" not in line:
            line += f" Project={project}"

        updated.append(line)

    return "\n".join(updated)


# ----------------------------
# TEXT / NOTE CONSISTENCY
# ----------------------------

def apply_text_consistency(content, context):
    """
    Replace generic placeholders or inject consistent fake entities
    into internal notes / text files.
    """
    chosen_name = random.choice(context["employee_names"])
    chosen_project = random.choice(context["project_names"])
    chosen_department = random.choice(context["departments"])

    content = content.replace("[EMPLOYEE]", chosen_name)
    content = content.replace("[PROJECT]", chosen_project)
    content = content.replace("[DEPARTMENT]", chosen_department)

    return content


# ----------------------------
# JSON CONSISTENCY
# ----------------------------

def apply_json_consistency(content, context):
    """
    Ensure JSON records align with fake organization context.
    """
    try:
        data = json.loads(content)
        if not isinstance(data, list):
            return content

        for item in data:
            if not isinstance(item, dict):
                continue

            chosen_name = random.choice(context["employee_names"])
            chosen_department = random.choice(context["departments"])
            chosen_email = name_to_email(chosen_name, context["email_domains"])
            chosen_project = random.choice(context["project_names"])

            for key in item.keys():
                k = key.lower()

                if "name" in k:
                    item[key] = chosen_name
                elif "department" in k:
                    item[key] = chosen_department
                elif "email" in k:
                    item[key] = chosen_email
                elif "username" in k:
                    item[key] = name_to_username(chosen_name)
                elif "project" in k:
                    item[key] = chosen_project

        return json.dumps(data, indent=4)

    except:
        return content


# ----------------------------
# MAIN ENTRY FUNCTION
# ----------------------------

def apply(content, metadata):
    """
    Main consistency application function.
    Applies cross-file / cross-entity consistency
    based on file type and fake organization context.
    """
    context = load_global_context()
    file_type = metadata.get("file_type", "").lower()
    content_type = metadata.get("content_type", "").lower()

    if file_type == "csv":
        return apply_csv_consistency(content, metadata, context)

    elif file_type == "json":
        return apply_json_consistency(content, context)

    elif file_type == "txt":
        if content_type == "credentials":
            return apply_credentials_consistency(content, context)
        elif content_type == "logs":
            return apply_log_consistency(content, context)
        else:
            return apply_text_consistency(content, context)

    elif file_type == "log":
        return apply_log_consistency(content, context)

    return content