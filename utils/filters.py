from typing import Dict, Set


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

    def should_ignore_noise(self, event: Dict) -> bool:
        data = event.get("data", {})
        pid = int(data.get("pid") or -1)
        name = str(data.get("process_name") or "").strip().lower()
        if pid in self._ignored_pids:
            return True
        return name in self._ignored_names

    def apply_known_process_logic(self, event: Dict, detection: Dict) -> bool:
        data = event.get("data", {})
        process_name = str(data.get("process_name") or "").lower()
        is_known = process_name in self._trusted_processes
        data["is_known"] = is_known

        if is_known and detection.get("score", 0) < self._trusted_low_score_allow:
            return False
        return True
