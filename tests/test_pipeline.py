# test_pipeline.py
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# test_pipeline.py


from agents.deployment.deployment_agent import DeploymentManager
from core.interception_layer import InterceptionLayer
from agents.generation.generation_agent import GenerationAgent


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
                    "realism": "medium",
                    "size_bytes_target": 5000
                }
            ]
        }
    }


def get_mock_analysis(intent, stage, confidence):
    return {
        "intent": intent,
        "attack_stage": stage,
        "confidence": confidence
    }


def run_test():

    print("\n🚀 Running PRE-GENERATION PIPELINE\n")

    # 1️⃣ Deployment
    deployment_manager = DeploymentManager()
    strategy_output = get_mock_strategy_output()
    deployment_state = deployment_manager.deploy(strategy_output)

    # 2️⃣ Interception + Generation
    generation_agent = GenerationAgent()
    interception = InterceptionLayer(generation_agent=generation_agent)

    # 🔥 Force execution immediately
    analysis = get_mock_analysis("data_exfiltration", "collection", 0.9)

    generated_files = {}

    for path in deployment_state["decoy_registry"]:

        input_data = {
            "path": path,
            "analysis": analysis,
            "deployment": deployment_state
        }

        result = interception.handle(input_data)

        generated_files[path] = result

    # 3️⃣ Print results
    print("\n📂 GENERATED FILES:\n")

    for path, content in generated_files.items():
        print(f"\n=== {path} ===")
        print(content)
        print("-" * 50)


if __name__ == "__main__":
    run_test()