import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import time

from agents.deployment.deployment_agent import DeploymentManager
from agents.generation.generation_agent import GenerationAgent
from core.interception_layer import InterceptionLayer
from core.path_resolver import normalize_path

from collectors.file_collector import FileCollector


def get_mock_strategy_output():
    return {
        "execution_plan": {
            "files_to_create": [
                {
                    "absolute_path": "D:\\shared\\logs\\sec_audit.log",
                    "file_type": "log",
                    "content_profile": "logs",
                    "realism": "medium",
                    "size_bytes_target": 5000
                }
            ]
        }
    }


def get_mock_analysis():
    return {
        "intent": "data_exfiltration",
        "attack_stage": "collection",
        "confidence": 0.9
    }


def main():

    print("\n🚀 Starting Event-Driven Pipeline\n")

    # ------------------------
    # 1️⃣ Deployment
    # ------------------------
    deployment_manager = DeploymentManager()
    deployment_state = deployment_manager.deploy(get_mock_strategy_output())

    # ------------------------
    # 2️⃣ Setup agents
    # ------------------------
    generation_agent = GenerationAgent()
    interception = InterceptionLayer(generation_agent=generation_agent)

    # ------------------------
    # 3️⃣ Start collector
    # ------------------------
    collector = FileCollector(path="D:\\shared", recursive=True)
    print("Watching path:", collector.path)

    print("👀 Watching for file events...\n")

    try:
        while True:
            events = collector.collect()

            for event in events:
           
                print("RAW EVENT:", event)

                raw_path = event["data"]["file_path"]

                print("\n📥 EVENT DETECTED:", raw_path)

                input_data = {
                    "path": raw_path,
                    "analysis": get_mock_analysis(),
                    "deployment": deployment_state
                }

                result = interception.handle(input_data)

                print("🧠 INTERCEPTION RESULT:")
                print(result[:300])  # don’t spam logs

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
        collector.stop()


if __name__ == "__main__":
    main()