# agents/deployment/context_builder.py

import random
import time


FIRST_NAMES = [
    "Amit", "Riya", "Karan", "Neha", "Arjun", "Sneha",
    "Rahul", "Priya", "Vikas", "Ananya"
]

LAST_NAMES = [
    "Sharma", "Jain", "Mehta", "Verma", "Gupta",
    "Agarwal", "Singh", "Kapoor", "Bansal", "Malhotra"
]

DEPARTMENTS = [
    "Finance",
    "HR",
    "Engineering",
    "Sales",
    "Marketing",
    "Operations",
    "IT Support",
    "Legal",
    "Procurement"
]

PROJECTS = ["Phoenix", "Orion", "Atlas", "Nimbus", "Zenith"]


def _generate_employee_names(n=5):
    names = set()

    while len(names) < n:
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        names.add(name)

    return list(names)


def _generate_emails(names, domain):
    emails = []

    for name in names:
        username = name.lower().replace(" ", ".")
        emails.append(f"{username}@{domain}")

    return emails


def _generate_timestamps():
    """
    Generate realistic past timestamps
    """
    now = time.time()
    days_ago = random.randint(10, 120)

    created_at = now - days_ago * 86400
    modified_at = created_at + random.randint(1, 30) * 86400

    return {
        "created_at": created_at,
        "modified_at": modified_at
    }


def build_global_context():
    """
    Builds a consistent fake organization context
    used across all generated files
    """

    # 🔹 dynamic organization identity
    company_domains = ["corp.local", "internal.net", "enterprise.local"]
    domain = random.choice(company_domains)

    # 🔹 generate employees
    employee_names = _generate_employee_names(n=5)

    # 🔹 assign departments randomly
    employee_map = {
        name: random.choice(DEPARTMENTS)
        for name in employee_names
    }

    # 🔹 generate emails
    emails = _generate_emails(employee_names, domain)

    return {
        "employee_names": employee_names,
        "employee_departments": employee_map,
        "emails": emails,
        "departments": DEPARTMENTS,
        "projects": random.sample(PROJECTS, k=3),
        "email_domain": domain,
        "timestamps": _generate_timestamps()
    }