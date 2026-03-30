# core/interception_layer.py

from core.decision_engine import decide_action

class InterceptionLayer:

    def __init__(self, generation_agent=None):
        self.generation_agent = generation_agent
        self.SUPPORTED_TYPES = ["csv", "txt", "log", "json", "env"]

    # ------------------------
    # MAIN ENTRY
    # ------------------------

    def handle(self, input_data):

        path = input_data.get("path")
        analysis = input_data.get("analysis", {})
        deployment = input_data.get("deployment", {})

        registry = deployment.get("decoy_registry", {})
        rules = deployment.get("interception_rules", {})

        # ------------------------
        # 1️⃣ If no decoy → real
        # ------------------------
        if path not in registry:
            return self._read_real(path, reason="no_decoy")

        metadata = registry[path]
        file_type = metadata.get("file_type", "txt")

        # ------------------------
        # 2️⃣ Unsupported → real
        # ------------------------
        if file_type not in self.SUPPORTED_TYPES:
            return self._read_real(path, reason="unsupported_type")

        # ------------------------
        # 3️⃣ Decide action
        # ------------------------
        action = decide_action(
            path,
            metadata,
            rules,
            analysis,
            self.SUPPORTED_TYPES
        )

        # ------------------------
        # 4️⃣ Execute action
        # ------------------------
        if action == "real":
            return self._read_real(path, reason="decision_real")

        if action == "partial":
            real = self._read_real(path)
            fake = self._generate_fake(path, metadata, deployment)
            return self._blend(real, fake)

        if action == "fake":
            return self._generate_fake(path, metadata, deployment)

        return self._read_real(path, reason="fallback")

    # ------------------------
    # HELPERS
    # ------------------------

    def _generate_fake(self, path, metadata, deployment):
        if not self.generation_agent:
            return "[ERROR] No generation agent available"

        result=self.generation_agent.generate(path, metadata)

        return result['content']

    def _read_real(self, path, reason=None):
        if reason:
            return f"[REAL:{reason}] {path}"
        return f"[REAL] {path}"

    def _blend(self, real, fake):
        return f"{real}\n---PARTIAL-DECEPTION---\n{fake}"