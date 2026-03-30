from agents.generation.generation_agent import generate


def run_test_case(path, metadata):
    print("=" * 80)
    print(f"REQUESTED PATH: {path}")
    print(f"METADATA: {metadata}")
    print("-" * 80)

    result = generate(path, metadata)

    print(f"SUCCESS : {result['success']}")
    print(f"SOURCE  : {result['source']}")
    print(f"SCHEMA  : {result['schema']}")
    print(f"REASON  : {result['reason']}")
    print("-" * 80)
    print("GENERATED CONTENT:\n")
    print(result["content"])
    print("=" * 80)
    print("\n\n")


if __name__ == "__main__":
    # -----------------------------
    # TEST CASE 1: Payroll CSV
    # -----------------------------
    run_test_case(
        path="/shared/finance/payroll_march.csv",
        metadata={
            "file_type": "csv",
            "content_type": "salary_data",
            "size": "medium",
            "realism_level": "high",
            "use_llm_realism": False,
            "columns": ["employee_id", "name", "salary", "department", "email"]
        }
    )

    # -----------------------------
    # TEST CASE 2: Credentials TXT
    # -----------------------------
    run_test_case(
        path="/shared/admin/backup_credentials.txt",
        metadata={
            "file_type": "txt",
            "content_type": "credentials",
            "size": "small",
            "realism_level": "medium",
            "use_llm_realism": True
        }
    )

    # -----------------------------
    # TEST CASE 3: Logs
    # -----------------------------
    run_test_case(
        path="/shared/logs/security_audit.log",
        metadata={
            "file_type": "log",
            "content_type": "logs",
            "size": "medium",
            "realism_level": "high",
            "use_llm_realism": True
        }
    )

    # -----------------------------
    # TEST CASE 4: Internal Note
    # -----------------------------
    run_test_case(
        path="/shared/operations/vendor_notes.txt",
        metadata={
            "file_type": "txt",
            "content_type": "internal_note",
            "size": "small",
            "realism_level": "high",
            "use_llm_realism": True
        }
    )

    # -----------------------------
# TEST CASE 6: ENV File
# -----------------------------
    run_test_case(
        path="/shared/config/.env",
        metadata={
            "file_type": "txt",
            "content_type": "env",
            "size": "small",
            "realism_level": "high",
            "use_llm_realism": True
        }
    )
    # -----------------------------
    # TEST CASE 5: JSON Data
    # -----------------------------
    run_test_case(
        path="/shared/hr/employee_archive.json",
        metadata={
            "file_type": "json",
            "content_type": "employee_data",
            "size": "medium",
            "realism_level": "medium",
            "use_llm_realism": True,
            "columns": ["employee_id", "name", "department", "email", "role"]
        }
    )