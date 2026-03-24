import subprocess
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Optional, Set


class AuthCollector:
    def __init__(self, max_events_per_poll: int = 50):
        self.max_events_per_poll = max_events_per_poll
        self._seen_record_ids: Set[int] = set()

    def collect(self) -> List[Dict]:
        events: List[Dict] = []
        xml_data = self._query_security_log()
        if not xml_data:
            return events

        parsed_rows = self._parse_events(xml_data)
        # wevtutil /rd:true returns newest first; emit older unseen first for stable ordering.
        parsed_rows.reverse()

        for row in parsed_rows:
            record_id = row.get("record_id")
            if record_id is None or record_id in self._seen_record_ids:
                continue

            self._seen_record_ids.add(record_id)
            if len(self._seen_record_ids) > 5000:
                # Keep memory bounded while preserving recent dedupe behavior.
                self._seen_record_ids = set(sorted(self._seen_record_ids)[-2500:])

            events.append(
                {
                    "type": "login_attempt",
                    "timestamp": float(row.get("timestamp") or time.time()),
                    "data": {
                        "username": row.get("username") or "unknown",
                        "source_ip": row.get("source_ip") or "",
                        "status": row.get("status") or "failed",
                    },
                }
            )

        return events

    def _query_security_log(self) -> str:
        query = "*[System[(EventID=4624 or EventID=4625)]]"
        cmd = [
            "wevtutil",
            "qe",
            "Security",
            f"/q:{query}",
            "/f:xml",
            f"/c:{self.max_events_per_poll}",
            "/rd:true",
        ]
        try:
            completed = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=8,
                check=False,
            )
            if completed.returncode != 0:
                return ""
            return completed.stdout or ""
        except Exception:
            return ""

    def _parse_events(self, raw_xml: str) -> List[Dict]:
        rows: List[Dict] = []
        try:
            root = ET.fromstring(raw_xml)
        except ET.ParseError:
            return rows

        event_nodes = [node for node in root if self._strip_ns(node.tag) == "Event"]
        for event in event_nodes:
            try:
                system = self._find_child_by_tag(event, "System")
                event_data = self._find_child_by_tag(event, "EventData")
                if system is None:
                    continue

                event_id_text = self._get_child_text(system, "EventID")
                record_id_text = self._get_child_text(system, "EventRecordID")
                if not event_id_text or not record_id_text:
                    continue

                event_id = int(event_id_text)
                status = "success" if event_id == 4624 else "failed"

                timestamp_node = self._find_child_by_tag(system, "TimeCreated")
                timestamp_raw = ""
                if timestamp_node is not None:
                    timestamp_raw = str(timestamp_node.attrib.get("SystemTime") or "")

                username = "unknown"
                source_ip = ""
                if event_data is not None:
                    username = self._read_named_data(event_data, "TargetUserName") or "unknown"
                    source_ip = self._read_named_data(event_data, "IpAddress") or ""
                    if source_ip in {"::1", "-"}:
                        source_ip = "127.0.0.1" if source_ip == "::1" else ""

                rows.append(
                    {
                        "record_id": int(record_id_text),
                        "timestamp": self._parse_windows_timestamp(timestamp_raw),
                        "username": username,
                        "source_ip": source_ip,
                        "status": status,
                    }
                )
            except Exception:
                continue

        return rows

    def _find_child_by_tag(self, node: ET.Element, local_tag: str) -> Optional[ET.Element]:
        for child in node:
            if self._strip_ns(child.tag) == local_tag:
                return child
        return None

    def _get_child_text(self, node: ET.Element, local_tag: str) -> str:
        child = self._find_child_by_tag(node, local_tag)
        return (child.text or "").strip() if child is not None else ""

    def _read_named_data(self, event_data: ET.Element, name: str) -> str:
        for child in event_data:
            if self._strip_ns(child.tag) != "Data":
                continue
            if str(child.attrib.get("Name") or "") == name:
                return (child.text or "").strip()
        return ""

    def _strip_ns(self, tag: str) -> str:
        return tag.split("}", 1)[1] if "}" in tag else tag

    def _parse_windows_timestamp(self, system_time: str) -> float:
        if not system_time:
            return time.time()
        # Examples: 2026-03-24T12:00:01.1234567Z
        try:
            if system_time.endswith("Z"):
                system_time = system_time[:-1] + "+00:00"
            if "." in system_time and "+" in system_time:
                left, tz = system_time.split("+", 1)
                date_part, frac = left.split(".", 1)
                frac = (frac + "000000")[:6]
                system_time = f"{date_part}.{frac}+{tz}"
            return datetime.fromisoformat(system_time).timestamp()
        except Exception:
            return time.time()
