import time
from typing import Dict, List

import psutil


class NetworkCollector:
    def collect(self) -> List[Dict]:
        events: List[Dict] = []
        now = time.time()

        try:
            connections = psutil.net_connections(kind="inet")
        except Exception:
            return events

        for conn in connections:
            try:
                pid = conn.pid
                process_name = "unknown"
                if pid:
                    try:
                        process_name = psutil.Process(pid).name() or "unknown"
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        process_name = "unknown"

                local_ip = ""
                remote_ip = ""
                remote_port = 0

                if conn.laddr:
                    local_ip = str(getattr(conn.laddr, "ip", "") or "")
                if conn.raddr:
                    remote_ip = str(getattr(conn.raddr, "ip", "") or "")
                    remote_port = int(getattr(conn.raddr, "port", 0) or 0)

                event = {
                    "type": "network_connection",
                    "timestamp": now,
                    "data": {
                        "pid": pid or 0,
                        "process_name": process_name,
                        "local_ip": local_ip,
                        "remote_ip": remote_ip,
                        "remote_port": remote_port,
                        "status": str(conn.status or "unknown"),
                    },
                }
                events.append(event)
            except Exception:
                continue

        return events
