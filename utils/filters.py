from typing import Dict, Set
import ipaddress


class EventFilter:
    def __init__(self):
        self._ignored_pids: Set[int] = {0}
        self._ignored_names = {"system idle process", "system", "registry"}
        self._trusted_processes = {
            "msedge.exe",
            "chrome.exe",
            "googledrivefs.exe",
            "cursor.exe",
            "code.exe",
            "explorer.exe",
            "services.exe",
            "svchost.exe",
            "lsass.exe",
            "csrss.exe",
            "wininit.exe",
            "smss.exe",
            "dwm.exe",
            "fontdrvhost.exe",
            "conhost.exe",
            "searchindexer.exe",
            "runtimebroker.exe",
            "spoolsv.exe",
            "taskhostw.exe",
        }
        self._trusted_low_score_allow = 5
        self._ignored_file_path_terms = {"node_modules", ".git", "cache", "tmp"}
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

    def should_ignore_noise(self, event: Dict) -> bool:
        event_type = event.get("type")
        data = event.get("data", {})

        if event_type == "file_access":
            file_path = str(data.get("file_path") or "").lower()
            return any(term in file_path for term in self._ignored_file_path_terms)

        if event_type == "network_connection":
            remote_ip = str(data.get("remote_ip") or "").strip()
            process_name = str(data.get("process_name") or "").lower().strip()
            if process_name in self._trusted_network_processes:
                return True
            return self._is_local_ip(remote_ip)

        if event_type == "login_attempt":
            return False

        pid = int(data.get("pid") or -1)
        name = str(data.get("process_name") or "").strip().lower()
        if pid in self._ignored_pids:
            return True
        return name in self._ignored_names

    def apply_known_process_logic(self, event: Dict, detection: Dict) -> bool:
        if event.get("type") != "process_start" and event.get("type") != "process_sample":
            return True

        data = event.get("data", {})
        process_name = str(data.get("process_name") or "").lower()
        is_known = process_name in self._trusted_processes
        data["is_known"] = is_known

        if is_known and detection.get("score", 0) < self._trusted_low_score_allow:
            return False
        return True

    def _is_local_ip(self, ip_value: str) -> bool:
        if not ip_value:
            return True
        try:
            ip = ipaddress.ip_address(ip_value)
            return ip.is_loopback or ip.is_private
        except ValueError:
            return False