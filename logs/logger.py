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

        event_type = event.get("type")
        if event_type == "file_access":
            self._emit_file_alert(event, detection)
            return

        if event_type == "network_connection":
            self._emit_network_alert(event, detection)
            return

        self._emit_process_alert(event, detection)

    def _emit_process_alert(self, event: Dict, detection: Dict) -> None:
        data = event.get("data", {})
        pid = data.get("pid")
        process_name = data.get("process_name", "unknown")
        reasons = detection.get("reasons") or detection.get("rare_patterns") or ["behavioral anomaly"]
        primary_reason = reasons[0]
        key = f"process:{primary_reason}:{pid}"

        if not self._check_rate_limit(key):
            return

        print("[ALERT] Suspicious Process Detected")
        print(f"Process: {process_name}")
        print(f"PID: {pid}")
        print(f"Parent: {data.get('parent_process') or 'unknown'}")
        print(f"CPU: {float(data.get('cpu_percent') or 0.0):.1f}%")
        print(f"Memory: {float(data.get('memory_mb') or 0.0):.1f} MB")
        print(f"Score: {detection.get('score', 0)}")
        print(f"Reason: {', '.join(reasons)}")
        print("-" * 50)

    def _emit_file_alert(self, event: Dict, detection: Dict) -> None:
        data = event.get("data", {})
        file_path = data.get("file_path", "unknown")
        action = data.get("action", "unknown")
        reasons = detection.get("reasons") or ["suspicious file behavior"]
        primary_reason = reasons[0]
        key = f"file:{primary_reason}:{file_path}:{action}"

        if not self._check_rate_limit(key):
            return

        print("[ALERT] Suspicious File Activity")
        print(f"File: {file_path}")
        print(f"Action: {action}")
        print(f"Score: {detection.get('score', 0)}")
        print(f"Reason: {', '.join(reasons)}")
        print("-" * 50)

    def _emit_network_alert(self, event: Dict, detection: Dict) -> None:
        data = event.get("data", {})
        process_name = data.get("process_name", "unknown")
        remote_ip = data.get("remote_ip", "")
        remote_port = data.get("remote_port", 0)
        reasons = detection.get("reasons") or ["suspicious network behavior"]
        primary_reason = reasons[0]
        key = f"network:{primary_reason}:{process_name}:{remote_ip}:{remote_port}"

        if not self._check_rate_limit(key):
            return

        print("[ALERT] Suspicious Network Activity")
        print(f"Process: {process_name}")
        print(f"Remote IP: {remote_ip or 'unknown'}")
        print(f"Port: {remote_port}")
        print(f"Score: {detection.get('score', 0)}")
        print(f"Reason: {', '.join(reasons)}")
        print("-" * 50)

    def _check_rate_limit(self, key: str) -> bool:
        now = time.time()
        last = self._last_emit_by_key.get(key, 0)
        if now - last < self.rate_limit_seconds:
            return False
        self._last_emit_by_key[key] = now
        return True