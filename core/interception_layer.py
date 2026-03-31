# core/interception_layer.py

from core.decision_engine import decide_action
from core.path_resolver import normalize_path, resolve_path
import os

class InterceptionLayer:

    def __init__(self, generation_agent=None):
        self.generation_agent = generation_agent
        self.SUPPORTED_TYPES = ["csv", "txt", "log", "json", "env","sql"]
        self._allowed_real_roots = self._build_allowed_real_roots()

    def _build_allowed_real_roots(self):
        roots = []

        # Default: keep real reads scoped to project-controlled roots.
        for rel in ("shared", "demo_shared"):
            try:
                roots.append(os.path.abspath(os.path.join(os.getcwd(), rel)))
            except Exception:
                continue

        # Optional extra roots (semicolon-separated on Windows).
        extra = os.environ.get("REAL_READ_ROOTS")
        if extra:
            for part in extra.split(";"):
                part = part.strip()
                if not part:
                    continue
                try:
                    roots.append(os.path.abspath(part))
                except Exception:
                    continue

        normed = []
        seen = set()
        for r in roots:
            rr = os.path.normcase(os.path.abspath(r))
            if rr in seen:
                continue
            seen.add(rr)
            normed.append(rr)
        return normed

    def _is_within_allowed_root(self, candidate_path: str) -> bool:
        try:
            cp = os.path.normcase(os.path.abspath(candidate_path))
        except Exception:
            return False
        for root in self._allowed_real_roots:
            try:
                if cp == root or cp.startswith(root + os.sep):
                    return True
            except Exception:
                continue
        return False

    def _resolve_real_read_path(self, original_path: str):
        """
        Resolve a "real" file path safely.

        - If a virtual path like /shared/... is provided, map it into ./shared/...
        - If an OS path is provided, only allow reading if it is within approved roots.
        """
        if not original_path or not isinstance(original_path, str):
            return None

        p = original_path.strip()
        if not p:
            return None

        if p.startswith("/"):
            parts = [x for x in p.split("/") if x]
            if parts and parts[0].lower() in {"shared", "demo_shared"}:
                mapped = os.path.abspath(os.path.join(os.getcwd(), *parts))
                return mapped if self._is_within_allowed_root(mapped) else None
            return None

        try:
            abs_p = os.path.abspath(p)
        except Exception:
            return None
        return abs_p if self._is_within_allowed_root(abs_p) else None

    # ------------------------
    # MAIN ENTRY
    # ------------------------

    def handle(self, input_data):

        original_path = input_data.get("path")
        path = normalize_path(original_path)
        analysis = input_data.get("analysis", {})
        deployment = input_data.get("deployment", {})

        registry = deployment.get("decoy_registry", {})
        rules = deployment.get("interception_rules", {})

        # ------------------------
        # 1️⃣ If no decoy → real
        # ------------------------
        if path not in registry:
            return self._read_real(original_path, reason="no_decoy")

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
        print("DECISION:", action)

        # ------------------------
        # 4️⃣ Execute action
        # ------------------------
        if action == "real":
            return self._read_real(original_path, reason="decision_real")

        if action == "fake":
            return self._generate_fake(path, metadata, deployment,analysis)

        return self._read_real(original_path, reason="fallback")

    # ------------------------
    # HELPERS
    # ------------------------

    def _generate_fake(self, path, metadata, deployment,analysis):
        if not self.generation_agent:
            return "[ERROR] No generation agent available"

        enriched_metadata = {
            **metadata,
            "analysis": analysis   # inject here
        }
        result=self.generation_agent.generate(path, enriched_metadata)

        return result['content']

    def _read_real(self, path, reason=None):
        resolved = self._resolve_real_read_path(path)
        if not resolved:
            blocked_msg = f"[REAL:blocked_outside_allowed_root] {path}"
            if reason:
                return f"[REAL:{reason}]\n{blocked_msg}"
            return blocked_msg

        real_path = resolved

        if not os.path.exists(real_path):
            return f"[REAL:missing] {path}"

        content = None
        for enc in ["utf-8", "utf-16"]:
            try:
                with open(real_path, "r", encoding=enc) as f:
                    content = f.read()
                    break
            except:
                continue

        if content is None:
            return f"[REAL:binary_or_unsupported] {path}"

        if reason:
            return f"[REAL:{reason}]\n{content}"

        return content

    # Partial deception intentionally removed: only REAL or FAKE responses are supported.
