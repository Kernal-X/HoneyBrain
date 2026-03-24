import re
import time
import ipaddress
from collections import deque
from typing import Dict, List


class ScoringDetector:
    def __init__(self, alert_threshold: int = 4, suspicious_threshold: int = 3):
        self.alert_threshold = alert_threshold
        self.suspicious_threshold = suspicious_threshold
        self._powershell_processes = {"powershell.exe", "pwsh.exe"}
        self._trusted_parents_for_powershell = {
            "explorer.exe",
            "cmd.exe",
            "powershell.exe",
            "pwsh.exe",
            "code.exe",
            "cursor.exe",
            "windowsterminal.exe",
            "conhost.exe",
            "services.exe",
            "svchost.exe",
        }
        self._suspicious_cmd_patterns = [
            re.compile(r"-enc(odedcommand)?\b", re.IGNORECASE),
            re.compile(r"\bfrombase64string\b", re.IGNORECASE),
            re.compile(r"\bdownloadstring\b", re.IGNORECASE),
            re.compile(r"\\temp\\|/tmp/", re.IGNORECASE),
        ]
        self._office_parents = {"winword.exe", "excel.exe", "powerpnt.exe", "outlook.exe"}
        self._browser_parents = {"chrome.exe", "msedge.exe", "firefox.exe", "iexplore.exe"}
        self._script_children = {"powershell.exe", "pwsh.exe", "cmd.exe", "wscript.exe", "cscript.exe", "python.exe"}
        self._sensitive_file_terms = ["password", "secret", ".env", "ssh", "key"]
        self._suspicious_dir_terms = ["temp", "appdata", "startup"]
        self._file_burst_window_seconds = 60
        self._high_file_activity_threshold = 40
        self._high_copy_activity_threshold = 25
        self._recent_file_activity = deque()
        self._recent_created_files = deque()
        self._trusted_network_processes = {
            "chrome.exe",
            "msedge.exe",
            "msedgewebview2.exe",
            "explorer.exe",
            "teams.exe",
            "ms-teams.exe",
            "onedrive.exe",
            "googledrivefs.exe",
            "cursor.exe",
            "code.exe",
        }
        self._trusted_service_networks = {
            # Google
            ipaddress.ip_network("8.8.8.0/24"),
            ipaddress.ip_network("8.34.208.0/20"),
            ipaddress.ip_network("8.35.192.0/20"),
            # Cloudflare
            ipaddress.ip_network("1.1.1.0/24"),
            ipaddress.ip_network("1.0.0.0/24"),
            # Microsoft (commonly observed edge/service ranges)
            ipaddress.ip_network("13.107.0.0/16"),
            ipaddress.ip_network("40.64.0.0/10"),
            # AWS (common service edge range)
            ipaddress.ip_network("52.95.0.0/16"),
        }

    def analyze(self, event: Dict) -> Dict:
        event_type = event.get("type")
        if event_type == "file_access":
            return self._analyze_file_event(event)
        if event_type == "network_connection":
            return self._analyze_network_event(event)
        return self._analyze_process_event(event)

    def _analyze_file_event(self, event: Dict) -> Dict:
        data = event.get("data", {})
        file_path = str(data.get("file_path") or "").lower()
        action = str(data.get("action") or "").lower()
        event_time = float(event.get("timestamp") or time.time())

        score = 0
        reasons: List[str] = []

        self._record_file_activity(action, event_time)

        if any(term in file_path for term in self._sensitive_file_terms):
            score += 3
            reasons.append("Sensitive file access pattern")

        if any(term in file_path for term in self._suspicious_dir_terms):
            score += 2
            reasons.append("Suspicious directory activity")

        if action == "modified":
            score += 1
            reasons.append("File modified")

        if len(self._recent_file_activity) >= self._high_file_activity_threshold:
            score += 2
            reasons.append("High volume file activity")

        if len(self._recent_created_files) >= self._high_copy_activity_threshold:
            score += 3
            reasons.append("Possible mass file copy/transfer activity")

        severity = "none"
        if score >= self.alert_threshold:
            severity = "alert"
        elif score >= self.suspicious_threshold:
            severity = "suspicious"

        return {
            "score": score,
            "severity": severity,
            "reasons": reasons,
            "rare_patterns": [],
        }

    def _record_file_activity(self, action: str, event_time: float) -> None:
        self._recent_file_activity.append(event_time)
        if action == "created":
            self._recent_created_files.append(event_time)

        cutoff = event_time - self._file_burst_window_seconds
        while self._recent_file_activity and self._recent_file_activity[0] < cutoff:
            self._recent_file_activity.popleft()
        while self._recent_created_files and self._recent_created_files[0] < cutoff:
            self._recent_created_files.popleft()

    def _analyze_network_event(self, event: Dict) -> Dict:
        data = event.get("data", {})
        score = 0
        reasons: List[str] = []

        remote_ip = str(data.get("remote_ip") or "").strip()
        process_name = str(data.get("process_name") or "").lower().strip()
        remote_port = int(data.get("remote_port") or 0)

        # Ignore local/private traffic quickly to reduce noise.
        if self._is_local_or_private_ip(remote_ip):
            return {
                "score": 0,
                "severity": "none",
                "reasons": [],
                "rare_patterns": [],
            }

        # Ignore normal outbound traffic from known user/system applications.
        if process_name in self._trusted_network_processes:
            return {
                "score": 0,
                "severity": "none",
                "reasons": [],
                "rare_patterns": [],
            }

        if self._is_trusted_service_ip(remote_ip):
            return {
                "score": 0,
                "severity": "none",
                "reasons": [],
                "rare_patterns": [],
            }

        # External connection from an untrusted process is a weak signal by itself.
        if remote_ip:
            score += 1
            reasons.append("External connection from unknown process")

        # Hidden/missing process identity is stronger.
        if process_name in {"", "unknown"}:
            score += 2
            reasons.append("Unknown process making network connection")

        if remote_port and remote_port not in {80, 443}:
            score += 1
            reasons.append("Unusual port usage")

        severity = "none"
        if score >= self.alert_threshold:
            severity = "alert"
        elif score >= self.suspicious_threshold:
            severity = "suspicious"

        return {
            "score": score,
            "severity": severity,
            "reasons": reasons,
            "rare_patterns": [],
        }

    def _analyze_process_event(self, event: Dict) -> Dict:
        data = event.get("data", {})
        score = 0
        reasons: List[str] = []
        rare_patterns: List[str] = []

        process_name = (data.get("process_name") or "").lower()
        parent_name = (data.get("parent_process") or "").lower()
        if parent_name == process_name:
            parent_name = ""
        cmdline = data.get("cmdline") or ""
        cpu_percent = float(data.get("cpu_percent") or 0.0)
        memory_mb = float(data.get("memory_mb") or 0.0)

        if cpu_percent > 80:
            score += 2
            reasons.append(f"High CPU ({cpu_percent:.1f}%)")

        if memory_mb > 500:
            score += 2
            reasons.append(f"High memory ({memory_mb:.1f} MB)")

        if self._is_suspicious_command(cmdline):
            score += 3
            reasons.append("Suspicious command pattern")

        if process_name in self._powershell_processes and parent_name:
            if parent_name not in self._trusted_parents_for_powershell:
                score += 2
                reasons.append("PowerShell launched by untrusted parent")

        if self._is_unusual_parent_child(parent_name, process_name):
            score += 2
            reasons.append("Unusual parent-child relationship")
            if parent_name in self._office_parents and process_name in self._script_children:
                rare_patterns.append("Office -> Script interpreter")
            if parent_name in self._browser_parents and process_name in self._script_children:
                rare_patterns.append("Browser -> Script execution")

        severity = "none"
        if score >= self.alert_threshold:
            severity = "alert"
        elif score >= self.suspicious_threshold:
            severity = "suspicious"
        elif rare_patterns:
            severity = "rare"

        return {
            "score": score,
            "severity": severity,
            "reasons": reasons,
            "rare_patterns": rare_patterns,
        }

    def _is_suspicious_command(self, cmdline: str) -> bool:
        if not cmdline:
            return False
        return any(pattern.search(cmdline) for pattern in self._suspicious_cmd_patterns)

    def _is_unusual_parent_child(self, parent_name: str, process_name: str) -> bool:
        if not parent_name or not process_name:
            return False
        return (
            (parent_name in self._office_parents and process_name in self._script_children)
            or (parent_name in self._browser_parents and process_name in self._script_children)
        )

    def _is_local_or_private_ip(self, ip_value: str) -> bool:
        if not ip_value:
            return True
        ip_lower = ip_value.lower()
        if ip_lower.startswith(("127.", "192.168.", "10.", "172.", "::1")):
            return True
        try:
            ip = ipaddress.ip_address(ip_value)
            return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast
        except ValueError:
            return True

    def _is_trusted_service_ip(self, ip_value: str) -> bool:
        if not ip_value:
            return False
        try:
            ip = ipaddress.ip_address(ip_value)
            return any(ip in network for network in self._trusted_service_networks)
        except ValueError:
            return False