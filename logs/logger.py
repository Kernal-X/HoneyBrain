import time
from typing import Dict


class SOCLogger:
    def __init__(self, rate_limit_seconds: int = 30):
        self.rate_limit_seconds = rate_limit_seconds
        self._last_emit_by_key = {}

    def emit(self, event: Dict, detection: Dict) -> None:
        severity = detection.get("severity", "none")
        if severity not in {"alert", "suspicious"}:
            return

        data = event.get("data", {})
        pid = data.get("pid")
        process_name = data.get("process_name", "unknown")
        reasons = detection.get("reasons") or detection.get("rare_patterns") or ["behavioral anomaly"]
        primary_reason = reasons[0]
        key = f"{primary_reason}:{pid}"

        now = time.time()
        last = self._last_emit_by_key.get(key, 0)
        if now - last < self.rate_limit_seconds:
            return
        self._last_emit_by_key[key] = now

        print("[ALERT] Suspicious Process Detected")
        print(f"Process: {process_name}")
        print(f"PID: {pid}")
        print(f"Parent: {data.get('parent_process') or 'unknown'}")
        print(f"CPU: {float(data.get('cpu_percent') or 0.0):.1f}%")
        print(f"Memory: {float(data.get('memory_mb') or 0.0):.1f} MB")
        print(f"Score: {detection.get('score', 0)}")
        print(f"Reason: {', '.join(reasons)}")
        print("-" * 50)
