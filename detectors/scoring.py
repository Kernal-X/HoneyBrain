import re
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

    def analyze(self, event: Dict) -> Dict:
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
