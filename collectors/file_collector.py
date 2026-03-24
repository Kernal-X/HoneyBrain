import os
import time
import threading
from typing import Dict, List

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class _BufferedFileEventHandler(FileSystemEventHandler):
    def __init__(self, collector: "FileCollector"):
        super().__init__()
        self._collector = collector

    def on_created(self, event):
        if not event.is_directory:
            self._collector._push_event(event.src_path, "created")

    def on_modified(self, event):
        if not event.is_directory:
            self._collector._push_event(event.src_path, "modified")

    def on_deleted(self, event):
        if not event.is_directory:
            self._collector._push_event(event.src_path, "deleted")


class FileCollector:
    def __init__(self, path: str = ".", recursive: bool = True):
        self.path = os.path.abspath(path)
        self.recursive = recursive
        self._events: List[Dict] = []
        self._lock = threading.Lock()
        self._observer = Observer()
        self._handler = _BufferedFileEventHandler(self)
        self._started = False
        self.start()

    def _push_event(self, file_path: str, action: str) -> None:
        event = {
            "type": "file_access",
            "timestamp": time.time(),
            "data": {
                "file_path": str(file_path),
                "action": action,
            },
        }
        with self._lock:
            self._events.append(event)

    def start(self):
        if self._started:
            return
        self._observer.schedule(self._handler, self.path, recursive=self.recursive)
        self._observer.start()
        self._started = True

    def stop(self):
        if not self._started:
            return
        self._observer.stop()
        self._observer.join(timeout=2)
        self._started = False

    def collect(self) -> List[Dict]:
        with self._lock:
            events = self._events[:]
            self._events.clear()
        return events