import json


# -----------------------------------
# GENERIC HELPERS
# -----------------------------------

def is_non_empty(content):
    """
    Basic check: content should not be empty or whitespace only.
    """
    return isinstance(content, str) and len(content.strip()) > 0


def normalize_line_count(content):
    """
    Return number of non-empty lines.
    """
    return len([line for line in content.strip().split("\n") if line.strip()])


# -----------------------------------
# CSV VALIDATION
# -----------------------------------

def validate_csv(content, schema):
    """
    Validate CSV structure:
    - non-empty
    - header exists
    - header matches expected schema length
    - each row has same number of columns
    """
    if not is_non_empty(content):
        return False, "CSV content is empty"

    lines = [line.strip() for line in content.strip().split("\n") if line.strip()]
    if len(lines) < 2:
        return False, "CSV must contain header + at least 1 row"

    header = [h.strip() for h in lines[0].split(",")]
    if schema and len(header) != len(schema):
        return False, f"CSV header length mismatch: expected {len(schema)}, got {len(header)}"

    for i, line in enumerate(lines[1:], start=2):
        row = [v.strip() for v in line.split(",")]
        if len(row) != len(header):
            return False, f"CSV row {i} column mismatch: expected {len(header)}, got {len(row)}"

    return True, "CSV valid"


def validate_env(content):
    """
    Validate .env / config-style file.
    Expected pattern: KEY=VALUE
    """
    if not is_non_empty(content):
        return False, ".env content is empty"

    lines = [line.strip() for line in content.strip().split("\n") if line.strip()]
    if len(lines) == 0:
        return False, ".env file has no usable lines"

    valid_count = 0
    for line in lines:
        if "=" in line and not line.startswith("#"):
            valid_count += 1

    if valid_count < 3:
        return False, ".env file does not resemble a real config file"

    return True, ".env valid"

# -----------------------------------
# JSON VALIDATION
# -----------------------------------

def validate_json(content, schema):
    """
    Validate JSON structure:
    - parseable JSON
    - list of dicts preferred
    - optional schema key presence check
    """
    if not is_non_empty(content):
        return False, "JSON content is empty"

    try:
        data = json.loads(content)
    except Exception as e:
        return False, f"Invalid JSON parse: {str(e)}"

    if not isinstance(data, list):
        return False, "JSON must be a list of objects"

    if len(data) == 0:
        return False, "JSON list is empty"

    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            return False, f"JSON item {idx} is not an object"

        if schema:
            for field in schema:
                if field not in item:
                    return False, f"JSON item {idx} missing schema field: {field}"

    return True, "JSON valid"


# -----------------------------------
# CREDENTIAL FILE VALIDATION
# -----------------------------------

def validate_credentials(content):
    """
    Validate credentials-like file:
    Expected loose format:
    username : password (role)
    """
    if not is_non_empty(content):
        return False, "Credentials content is empty"

    lines = [line.strip() for line in content.strip().split("\n") if line.strip()]
    if len(lines) == 0:
        return False, "Credentials file has no usable lines"

    valid_count = 0
    for line in lines:
        if ":" in line:
            valid_count += 1

    if valid_count == 0:
        return False, "No credential-like entries found"

    return True, "Credentials valid"


# -----------------------------------
# LOG VALIDATION
# -----------------------------------

def validate_logs(content):
    """
    Validate log-like content:
    Should have multiple lines and some event-like structure.
    """
    if not is_non_empty(content):
        return False, "Log content is empty"

    lines = [line.strip() for line in content.strip().split("\n") if line.strip()]
    if len(lines) == 0:
        return False, "No log lines found"

    signal_count = 0
    for line in lines:
        if "Event=" in line or "[" in line or "User=" in line:
            signal_count += 1

    if signal_count == 0:
        return False, "Log file does not resemble operational logs"

    return True, "Logs valid"


# -----------------------------------
# TEXT / NOTE VALIDATION
# -----------------------------------

def validate_text(content):
    """
    Validate generic text note / memo / internal file.
    """
    if not is_non_empty(content):
        return False, "Text content is empty"

    line_count = normalize_line_count(content)
    if line_count == 0:
        return False, "Text file has no meaningful lines"

    return True, "Text valid"


# -----------------------------------
# BELIEVABILITY CHECKS (LIGHTWEIGHT)
# -----------------------------------

def lightweight_believability_check(content, metadata):
    """
    Optional lightweight sanity checks to avoid obviously broken outputs.
    This is NOT strict semantic validation — just quality filtering.
    """
    if not is_non_empty(content):
        return False, "Believability failed: empty content"

    # Avoid placeholder-heavy junk
    bad_markers = ["field1", "field2", "field3", "value_1", "value_2"]
    bad_hits = sum(marker in content for marker in bad_markers)

    if bad_hits >= 3:
        return False, "Believability failed: too many placeholder artifacts"

    # Avoid ultra-short fake files
    if len(content.strip()) < 15:
        return False, "Believability failed: content too short"

    return True, "Believability passed"


# -----------------------------------
# MAIN ENTRY FUNCTION
# -----------------------------------

def validate(content, metadata, schema=None):
    """
    Main validation entry point.
    Chooses validation logic based on file type + content type.
    Returns:
        (is_valid: bool, reason: str)
    """
    file_type = metadata.get("file_type", "").lower()
    content_type = metadata.get("content_type", "").lower()

    # 1. File-type-specific validation
    if file_type == "csv":
        valid, reason = validate_csv(content, schema)

    elif file_type == "json":
        valid, reason = validate_json(content, schema)

    elif file_type == "txt":
        if content_type == "credentials":
            valid, reason = validate_credentials(content)
        elif content_type == "logs":
            valid, reason = validate_logs(content)
        elif content_type == "env":
            valid, reason = validate_env(content)
        else:
            valid, reason = validate_text(content)

    elif file_type == "log":
        valid, reason = validate_logs(content)

    else:
        valid, reason = validate_text(content)

    if not valid:
        return False, reason

    # 2. Lightweight believability pass
    believable, b_reason = lightweight_believability_check(content, metadata)
    if not believable:
        return False, b_reason

    return True, "Validation passed"