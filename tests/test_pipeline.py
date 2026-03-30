# test_pipeline.py
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# test_pipeline.py

from agents.deployment.deployment_agent import DeploymentManager
from core.interception_layer import InterceptionLayer

# 🔥 USE YOUR REAL GENERATION AGENT
from agents.generation.generation_agent import GenerationAgent


# ------------------------
# Mock Strategy Output
# ------------------------
def get_mock_strategy_output():
    return {
        "execution_plan": {
            "files_to_create": [
                {
                    "absolute_path": "/shared/finance/payroll_march.csv",
                    "file_type": "csv",
                    "columns": ["employee_id", "name", "salary", "department", "email"],
                    "content_profile": "salary_data",
                    "realism": "high",
                    "size_bytes_target": 3000
                },
                {
                    "absolute_path": "/shared/admin/backup_credentials.txt",
                    "file_type": "txt",
                    "columns": [],
                    "content_profile": "credentials",
                    "realism": "medium",
                    "size_bytes_target": 800
                },
                {
                    "absolute_path": "/shared/logs/security_audit.log",
                    "file_type": "log",
                    "columns": [],
                    "content_profile": "logs",
                    "realism": "high",
                    "size_bytes_target": 5000
                },
                {
                    "absolute_path": "/shared/config/.env",
                    "file_type": "env",
                    "columns": [],
                    "content_profile": "env",
                    "realism": "high",
                    "size_bytes_target": 600
                },
                {
                    "absolute_path": "/shared/hr/employee_archive.json",
                    "file_type": "json",
                    "columns": ["employee_id", "name", "department", "email", "role"],
                    "content_profile": "employee_data",
                    "realism": "medium",
                    "size_bytes_target": 2500
                }
            ]
        }
    }


# ------------------------
# Mock Analysis Output
# ------------------------
def get_mock_analysis(intent, stage, confidence):
    return {
        "intent": intent,
        "attack_stage": stage,
        "confidence": confidence
    }


# ------------------------
# Mock Event
# ------------------------
def get_mock_event(path):
    return {
        "type": "file_access",
        "timestamp": "now",
        "data": {
            "path": path,
            "user": "attacker",
            "process": "cat"
        }
    }


# ------------------------
# RUN TEST
# ------------------------
def run_test():

    print("\n🚀 Running REAL Generation Agent Test\n")

    # 1️⃣ Deployment
    deployment_manager = DeploymentManager()
    strategy_output = get_mock_strategy_output()

    deployment_state = deployment_manager.deploy(strategy_output)

    print("📦 Deployment State Built\n")
    print("="*60)

    # 2️⃣ Interception Layer with REAL generator
    generation_agent = GenerationAgent()

    interception = InterceptionLayer(
        generation_agent=generation_agent
    )

    # ------------------------
    # TEST CASES
    # ------------------------

    test_cases = [
        ("LOW CONFIDENCE → REAL", get_mock_analysis("reconnaissance", "discovery", 0.2)),
        ("MEDIUM CONFIDENCE → PARTIAL", get_mock_analysis("reconnaissance", "collection", 0.5)),
        ("HIGH CONFIDENCE → FAKE", get_mock_analysis("data_exfiltration", "exfiltration", 0.9)),
    ]

    test_paths = [
        "/shared/finance/payroll_march.csv",
        "/shared/admin/backup_credentials.txt",
        "/shared/logs/security_audit.log",
        "/shared/config/.env",
        "/shared/hr/employee_archive.json"
    ]

    for label, analysis in test_cases:

        print(f"\n🧪 TEST: {label}")

        for path in test_paths:

            event = get_mock_event(path)

            input_data = {
                "path": event["data"]["path"],
                "analysis": analysis,
                "deployment": deployment_state
            }

            result = interception.handle(input_data)

            print(f"\n📂 Path: {path}")
            print(result)
            print("-"*50)


# ------------------------
# ENTRY
# ------------------------
if __name__ == "__main__":
    run_test()