# core/interception_layer.py

class InterceptionLayer:

    def __init__(self, generation_agent=None):
        self.generation_agent = generation_agent

        # define supported types here (central control)
        self.SUPPORTED_TYPES = ["csv", "txt", "log", "json", "env"]

    # ------------------------
    # MAIN ENTRY
    # ------------------------

    def handle(self, input_data):
        """
        Main interception logic
        """

        path = input_data.get("path")
        state = input_data.get("aggregated_state", {})
        deployment = input_data.get("deployment", {})

        risk_score = state.get("risk_score", 0.0)
        intent = state.get("intent", "unknown")

        registry = deployment.get("decoy_registry", {})
        rules = deployment.get("interception_rules", {})

        # ------------------------
        # 1️⃣ If no decoy → return real
        # ------------------------
        if path not in registry:
            return self._read_real(path, reason="no_decoy")

        metadata = registry[path]
        file_type = metadata.get("file_type", "txt")

        # ------------------------
        # 2️⃣ Unsupported file → return real
        # ------------------------
        if file_type not in self.SUPPORTED_TYPES:
            return self._read_real(path, reason="unsupported_type")

        # ------------------------
        # 3️⃣ Get rules
        # ------------------------
        rule = rules.get(path, {})
        threshold = rule.get("risk_threshold", 0.7)
        mode = rule.get("deception_mode", "partial")

        # ------------------------
        # 4️⃣ Low risk → real
        # ------------------------
        if risk_score < 0.3:
            return self._read_real(path, reason="low_risk")

        # ------------------------
        # 5️⃣ Medium risk → partial deception
        # ------------------------
        if 0.3 <= risk_score < threshold:

            if mode == "partial" and self.generation_agent:
                real = self._read_real(path)
                fake = self._generate_fake(path, metadata, deployment)
                return self._blend(real, fake)

            return self._read_real(path, reason="medium_risk_no_deception")

        # ------------------------
        # 6️⃣ High risk → full deception
        # ------------------------
        if risk_score >= threshold:

            # optional: intent-based boost
            if intent in ["data_exfiltration", "reconnaissance"]:
                return self._generate_fake(path, metadata, deployment)

            # fallback to mode
            if mode == "full" and self.generation_agent:
                return self._generate_fake(path, metadata, deployment)

            return self._read_real(path, reason="high_risk_but_safe")

        # ------------------------
        # fallback (shouldn't happen)
        # ------------------------
        return self._read_real(path, reason="fallback")

    # ------------------------
    # HELPERS
    # ------------------------

    def _generate_fake(self, path, metadata, deployment):
        if not self.generation_agent:
            return "[ERROR] No generation agent available"

        return self.generation_agent.generate(path, metadata, deployment)

    def _read_real(self, path, reason=None):
        """
        Simulated real file read
        (replace later if needed)
        """
        if reason:
            return f"[REAL:{reason}] {path}"
        return f"[REAL] {path}"

    def _blend(self, real, fake):
        """
        Combine real + fake data
        """
        return f"{real}\n---PARTIAL-DECEPTION---\n{fake}"