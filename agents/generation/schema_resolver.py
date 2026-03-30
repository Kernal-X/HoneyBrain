import os
from utils.llm_client import call_llm_json


# -----------------------------------
# DEFAULT SCHEMA LIBRARY
# -----------------------------------

DEFAULT_SCHEMAS = {
    "salary_data": ["employee_id", "name", "salary", "department", "email"],
    "employee_data": ["employee_id", "name", "department", "email", "role"],
    "vendor_data": ["vendor_name", "account_no", "bank_name", "payment_status"],
    "logs": ["timestamp", "level", "message"],
    "credentials": ["username", "password", "role"],
    "env": [
        "APP_ENV",
        "APP_NAME",
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
        "JWT_SECRET",
        "API_KEY",
        "AWS_ACCESS_KEY_ID",
        "SERVICE_OWNER",
        "DEBUG"
    ],

    # -----------------------------
    # SQL-specific / database-like
    # -----------------------------
    "database_dump": ["id", "name", "created_at", "status"],
    "user_accounts": ["user_id", "username", "email", "password_hash", "role", "created_at"],
    "payroll_db": ["employee_id", "name", "department", "salary", "bank_account", "tax_id"],
    "auth_data": ["user_id", "username", "email", "password_hash", "last_login", "is_active"]
}


# -----------------------------------
# SENSITIVITY-AWARE FALLBACKS
# -----------------------------------

import random


SENSITIVITY_SCHEMAS = {
    "low": [
        ["id", "name", "status", "created_at"],
        ["product_id", "product_name", "category", "price", "stock"],
        ["ticket_id", "subject", "priority", "status", "created_at"],
        ["asset_id", "asset_name", "owner", "location", "status"]
    ],

    "medium": [
        ["employee_id", "name", "email", "department", "role", "joining_date"],
        ["vendor_id", "vendor_name", "email", "bank_name", "payment_status"],
        ["project_id", "project_name", "owner", "team", "status", "deadline"],
        ["client_id", "client_name", "email", "region", "account_manager"],
        ["system_id", "hostname", "ip_address", "owner_team", "environment", "status"]
    ],

    "high": [
        # Payroll / financial
        ["employee_id", "full_name", "email", "salary", "bank_account", "tax_id"],

        # Auth / IAM
        ["user_id", "username", "email", "password_hash", "last_login", "is_active"],

        # Customer / PII
        ["customer_id", "full_name", "phone", "email", "account_number", "kyc_status"],

        # Infra / secrets
        ["service_name", "access_key", "secret_key", "owner", "created_at", "expires_at"],

        # Internal admin / privileged access
        ["admin_id", "username", "password_hash", "role", "mfa_enabled", "last_login"],

        # Database connection style
        ["db_name", "db_user", "db_password", "db_host", "db_port", "environment"],

        # API integration config
        ["integration_name", "api_key", "api_secret", "endpoint", "owner_team", "status"]
    ]
}


def infer_from_sensitivity(metadata, path=None):
    """
    Return a realistic fallback schema based on sensitivity.
    Uses filename/content hints to bias toward more believable schemas.
    """
    sensitivity = metadata.get("sensitivity", "medium").lower()
    content_type = metadata.get("content_type", "").lower()
    file_type = metadata.get("file_type", "").lower()
    filename = (path or "").lower()

    options = SENSITIVITY_SCHEMAS.get(sensitivity, SENSITIVITY_SCHEMAS["medium"])

    # -----------------------------
    # HIGH-SIGNAL BIASING
    # -----------------------------
    if sensitivity == "high":
        if any(x in filename for x in ["payroll", "salary", "compensation", "finance"]):
            return ["employee_id", "full_name", "email", "salary", "bank_account", "tax_id"]

        if any(x in filename for x in ["auth", "login", "account", "users", "admin", "iam"]):
            return ["user_id", "username", "email", "password_hash", "last_login", "is_active"]

        if any(x in filename for x in ["secret", "token", "key", "vault", "access", "credential"]):
            return ["service_name", "access_key", "secret_key", "owner", "created_at", "expires_at"]

        if any(x in filename for x in ["database", "db", "backup", "dump"]):
            return ["db_name", "db_user", "db_password", "db_host", "db_port", "environment"]

        if content_type in ["credentials", "auth_data"]:
            return ["user_id", "username", "email", "password_hash", "last_login", "is_active"]

    if sensitivity == "medium":
        if any(x in filename for x in ["employee", "staff", "hr"]):
            return ["employee_id", "name", "email", "department", "role", "joining_date"]

        if any(x in filename for x in ["vendor", "invoice", "payment"]):
            return ["vendor_id", "vendor_name", "email", "bank_name", "payment_status"]

        if any(x in filename for x in ["server", "system", "infra", "host"]):
            return ["system_id", "hostname", "ip_address", "owner_team", "environment", "status"]

    # -----------------------------
    # FILE-TYPE BIASING
    # -----------------------------
    if file_type == "env":
        if sensitivity == "high":
            return ["APP_ENV", "DB_HOST", "DB_USER", "DB_PASSWORD", "JWT_SECRET", "API_KEY"]
        return ["APP_ENV", "APP_NAME", "DEBUG", "SERVICE_OWNER"]

    if file_type == "log":
        if sensitivity == "high":
            return ["timestamp", "service", "user", "action", "ip_address", "status"]
        return ["timestamp", "level", "message"]

    # -----------------------------
    # RANDOM REALISTIC FALLBACK
    # -----------------------------
    return random.choice(options)


# -----------------------------------
# METADATA NORMALIZATION
# -----------------------------------

def normalize_metadata(metadata):
    """
    Normalize incoming metadata so downstream logic is consistent.
    """
    metadata = metadata or {}

    return {
        "file_type": str(metadata.get("file_type", "")).strip().lower(),
        "content_type": str(metadata.get("content_type", "")).strip().lower(),
        "size": str(metadata.get("size", "")).strip(),  # kept as-is; parsed elsewhere
        "sensitivity": str(metadata.get("sensitivity", "medium")).strip().lower(),
        "realism_level": str(metadata.get("realism_level", "medium")).strip().lower(),
        "use_llm_realism": bool(metadata.get("use_llm_realism", False)),
        "columns": metadata.get("columns", [])
    }


# -----------------------------------
# FILENAME HEURISTICS
# -----------------------------------

def infer_from_filename(path):
    filename = os.path.basename(path).lower()

    if "salary" in filename or "payroll" in filename:
        return DEFAULT_SCHEMAS["salary_data"]

    if "employee" in filename or "staff" in filename:
        return DEFAULT_SCHEMAS["employee_data"]

    if "vendor" in filename or "invoice" in filename:
        return DEFAULT_SCHEMAS["vendor_data"]

    if "credential" in filename or "password" in filename or "secret" in filename:
        return DEFAULT_SCHEMAS["credentials"]

    if filename == ".env" or "env" in filename or "config" in filename:
        return DEFAULT_SCHEMAS["env"]

    if "log" in filename or "audit" in filename:
        return DEFAULT_SCHEMAS["logs"]

    # -----------------------------
    # SQL / DB filename heuristics
    # -----------------------------
    if "dump" in filename or "backup" in filename or "db" in filename or "database" in filename:
        return DEFAULT_SCHEMAS["database_dump"]

    if "users" in filename or "accounts" in filename or "auth" in filename:
        return DEFAULT_SCHEMAS["user_accounts"]

    return []


# -----------------------------------
# SQL-SPECIFIC INFERENCE
# -----------------------------------

def infer_sql_schema(path, metadata):
    """
    Infer a likely SQL table schema based on content_type + filename + sensitivity.
    """
    content_type = metadata.get("content_type", "")
    sensitivity = metadata.get("sensitivity", "medium")
    filename = os.path.basename(path).lower()

    if content_type in DEFAULT_SCHEMAS:
        return DEFAULT_SCHEMAS[content_type]

    if "payroll" in filename or "salary" in filename:
        return DEFAULT_SCHEMAS["payroll_db"]

    if "auth" in filename or "user" in filename or "account" in filename:
        return DEFAULT_SCHEMAS["auth_data"]

    if sensitivity == "high":
        return ["record_id", "full_name", "email", "phone", "account_number", "created_at"]

    if sensitivity == "medium":
        return ["record_id", "name", "email", "department", "created_at"]

    return ["record_id", "name", "created_at", "status"]


# -----------------------------------
# LLM SCHEMA INFERENCE
# -----------------------------------

def infer_schema_with_llm(path, metadata):
    """
    Use LLM ONLY when deterministic schema resolution fails.
    Returns list[str] or [].
    """
    filename = os.path.basename(path)
    file_type = metadata.get("file_type", "")
    content_type = metadata.get("content_type", "")
    sensitivity = metadata.get("sensitivity", "medium")
    size = metadata.get("size", "")

    prompt = f"""
Infer a likely schema (field names / logical columns) for a deceptive enterprise file.

File path: {path}
Filename: {filename}
File type: {file_type}
Content type: {content_type}
Sensitivity: {sensitivity}
Approx size: {size}

Return ONLY valid JSON in this format:
{{
  "schema": ["field1", "field2", "field3"]
}}

Rules:
- Keep schema compact and realistic
- Match likely enterprise/internal data structure
- If file is logs-like, use operational log fields
- If file is credentials-like, use username/password style fields
- If file is config-like, use environment/config keys
- If file is SQL-like, return realistic table column names
- Higher sensitivity may include more personally identifiable or financial-looking fields
- Do not explain anything
"""

    result = call_llm_json(prompt)
    if result and isinstance(result, dict):
        schema = result.get("schema", [])
        if isinstance(schema, list) and len(schema) > 0:
            return [str(x).strip() for x in schema if str(x).strip()]

    return []


# -----------------------------------
# MAIN RESOLVER
# -----------------------------------

def resolve(path, metadata):
    """
    Resolve schema for fake artifact generation.

    Priority:
    1. Explicit metadata columns
    2. Known content_type schema
    3. SQL-specific inference (if file_type == sql)
    4. Filename heuristic
    5. Sensitivity-aware fallback
    6. LLM inference (ONLY if unresolved)
    7. File-type fallback
    """
    metadata = normalize_metadata(metadata)

    # 1. Explicit metadata schema
    if metadata["columns"]:
        return metadata["columns"]

    content_type = metadata["content_type"]
    file_type = metadata["file_type"]

    # 2. Known content type
    if content_type in DEFAULT_SCHEMAS:
        return DEFAULT_SCHEMAS[content_type]

    # 3. SQL-specific inference
    if file_type == "sql":
        sql_schema = infer_sql_schema(path, metadata)
        if sql_schema:
            return sql_schema

    # 4. Filename heuristic
    inferred = infer_from_filename(path)
    if inferred:
        return inferred

    # 5. Sensitivity-aware fallback
    sensitivity_schema = infer_from_sensitivity(metadata)
    if sensitivity_schema:
        fallback_candidate = sensitivity_schema
    else:
        fallback_candidate = []

    # 6. LLM fallback inference
    llm_schema = infer_schema_with_llm(path, metadata)
    if llm_schema:
        return llm_schema

    # 7. File-type fallback
    if file_type == "csv":
        return fallback_candidate or ["id", "name", "status"]

    elif file_type == "json":
        return fallback_candidate or ["id", "name", "status"]

    elif file_type == "sql":
        return fallback_candidate or ["id", "name", "created_at", "status"]

    elif file_type == "txt":
        if content_type == "credentials":
            return DEFAULT_SCHEMAS["credentials"]
        elif content_type == "logs":
            return DEFAULT_SCHEMAS["logs"]
        elif content_type == "env":
            return DEFAULT_SCHEMAS["env"]
        else:
            return ["note"]

    elif file_type == "log":
        return DEFAULT_SCHEMAS["logs"]

    return fallback_candidate or ["data"]