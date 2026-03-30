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
    ]
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

    return []


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

    prompt = f"""
Infer a likely schema (field names / logical columns) for a deceptive enterprise file.

File path: {path}
Filename: {filename}
File type: {file_type}
Content type: {content_type}

Return ONLY valid JSON in this format:
{{
  "schema": ["field1", "field2", "field3"]
}}

Rules:
- Keep schema compact and realistic
- If file is logs-like, use operational log fields
- If file is credentials-like, use username/password style fields
- If file is config-like, use environment/config keys
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
    3. Filename heuristic
    4. LLM inference (ONLY if unresolved)
    5. File-type fallback
    """
    # 1. Explicit metadata schema
    if "columns" in metadata and metadata["columns"]:
        return metadata["columns"]

    content_type = metadata.get("content_type", "").lower()
    file_type = metadata.get("file_type", "").lower()

    # 2. Known content type
    if content_type in DEFAULT_SCHEMAS:
        return DEFAULT_SCHEMAS[content_type]

    # 3. Filename heuristic
    inferred = infer_from_filename(path)
    if inferred:
        return inferred

    # 4. LLM fallback inference
    llm_schema = infer_schema_with_llm(path, metadata)
    if llm_schema:
        return llm_schema

    # 5. File-type fallback
    if file_type == "csv":
        return ["id", "name", "status"]

    elif file_type == "json":
        return ["id", "name", "status"]

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

    return ["data"]