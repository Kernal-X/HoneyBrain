# agents/deployment/deployment_agent.py

from agents.deployment.decoy_registry import DecoyRegistry
from agents.deployment.context_builder import build_global_context
from agents.deployment.rule_engine import build_interception_rules


class DeploymentManager:

    def __init__(self):
        self.registry = DecoyRegistry()
        self.global_context = {}
        self.interception_rules = {}

    def deploy(self, strategy_output):
        """
        Main entry point
        """

        self._build_registry(strategy_output)
        self.global_context = build_global_context()
        self.interception_rules = build_interception_rules(
            self.registry.get_all()
        )

        return self.get_state()

    # ------------------------
    # INTERNAL METHODS
    # ------------------------

    def _build_registry(self, strategy_output):

        SUPPORTED_TYPES = ["csv", "txt", "log", "json", "env"]

        files = strategy_output.get("execution_plan", {}).get("files_to_create", [])

        for file in files:
            file_type = file.get("file_type", "txt")

            # 🔥 FILTER UNSUPPORTED TYPES
            if file_type not in SUPPORTED_TYPES:
                print(f"[WARNING] Skipping unsupported file type: {file_type}")
                continue
            path = file.get("path")

            metadata = {
                "file_type": file.get("file_type", "txt"),
                "schema": file.get("columns", []),
                "realism": file.get("realism", "medium"),
                "use_llm_realism": file.get("realism", "medium") == "high",
                "sensitivity": self._infer_sensitivity(path)
            }

            self.registry.add(path, metadata)

    def _infer_sensitivity(self, path):

        if any(k in path.lower() for k in ["finance", "password", "secret"]):
            return "high"
        return "medium"

    # ------------------------
    # PUBLIC API
    # ------------------------

    def get_state(self):
        return {
            "decoy_registry": self.registry.get_all(),
            "global_context": self.global_context,
            "interception_rules": self.interception_rules
        }