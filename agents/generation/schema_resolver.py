from generation.cache import get_schema, set_schema


DEFAULT_SCHEMAS = {
    "employee_records": ["employee_id", "name", "department", "salary", "email"],
    "financial_records": ["employee_name", "account_no", "salary", "department"],
    "vendor_accounts": ["vendor_name", "account_no", "bank_name", "ifsc_code", "payment_status"],
    "credentials": ["username", "password", "role"],
    "logs": ["timestamp", "level", "message"]
}


def infer_schema_with_llm(path, metadata):
    """
    Placeholder for future LLM schema inference.
    For now, fallback to filename heuristics.
    """
    filename = path.lower()

    if "vendor" in filename:
        return DEFAULT_SCHEMAS["vendor_accounts"]
    elif "account" in filename or "finance" in filename:
        return DEFAULT_SCHEMAS["financial_records"]
    elif "employee" in filename or "hr" in filename:
        return DEFAULT_SCHEMAS["employee_records"]
    elif "cred" in filename or "password" in filename:
        return DEFAULT_SCHEMAS["credentials"]
    elif "log" in filename:
        return DEFAULT_SCHEMAS["logs"]

    return ["field1", "field2", "field3"]


def resolve(path, metadata):
    # 1. If explicit schema already exists in metadata
    if "schema" in metadata and metadata["schema"]:
        return metadata["schema"]

    # 2. Check schema cache
    cached_schema = get_schema(path)
    if cached_schema:
        return cached_schema

    # 3. Use content_type if known
    content_type = metadata.get("content_type", "")
    if content_type in DEFAULT_SCHEMAS:
        schema = DEFAULT_SCHEMAS[content_type]
        set_schema(path, schema)
        return schema

    # 4. Fallback inference
    schema = infer_schema_with_llm(path, metadata)
    set_schema(path, schema)
    return schema