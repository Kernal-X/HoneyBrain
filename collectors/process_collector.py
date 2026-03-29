import time
from typing import Dict, List, Optional

import psutil


class ProcessCollector:
    def __init__(self, interval: float = 1.0):
        self.interval = interval
        self._seen_pids = set()

    def _prime_cpu_counters(self) -> None:
        for proc in psutil.process_iter(["pid"]):
            try:
                proc.cpu_percent(interval=None)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

    def _get_parent_name(self, proc: psutil.Process) -> Optional[str]:
        try:
            parent = proc.parent()
            return parent.name() if parent else None
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return None

    def collect(self) -> List[Dict]:
        # Correct CPU sampling: prime counters, wait, then read actual values.
        self._prime_cpu_counters()
        time.sleep(self.interval)

        events: List[Dict] = []
        now = time.time()
        current_pids = set()

        for proc in psutil.process_iter(["pid", "name", "ppid", "cmdline", "username", "memory_info"]):
            try:
                info = proc.info
                pid = info.get("pid")
                if pid is None:
                    continue

                current_pids.add(pid)
                cmdline_parts = info.get("cmdline") or []
                cmdline = " ".join(cmdline_parts).strip()

                memory_info = info.get("memory_info")
                memory_mb = (memory_info.rss / (1024 * 1024)) if memory_info else 0.0

                exe_path: Optional[str] = None
                try:
                    exe_path = proc.exe()
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    exe_path = None

                event = {
                    "type": "process_start" if pid not in self._seen_pids else "process_sample",
                    "timestamp": now,
                    "data": {
                        "pid": pid,
                        "process_name": info.get("name") or "unknown",
                        "parent_pid": info.get("ppid"),
                        "parent_process": self._normalize_parent_name(info.get("name"), self._get_parent_name(proc)),
                        "cmdline": cmdline,
                        "cpu_percent": proc.cpu_percent(interval=None),
                        "memory_mb": round(memory_mb, 2),
                        "exe_path": exe_path,
                        "user": info.get("username") or "unknown",
                        "is_known": False,
                    },
                }
                events.append(event)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        self._seen_pids = current_pids
        return events

    def _normalize_parent_name(self, process_name: Optional[str], parent_name: Optional[str]) -> Optional[str]:
        if not process_name or not parent_name:
            return parent_name
        if process_name.strip().lower() == parent_name.strip().lower():
            return None
        return parent_name
