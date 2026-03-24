# core/monitor.py

from collectors.process_collector import ProcessCollector
from collectors.file_collector import FileCollector


class Monitor:
    def __init__(self, interval=1):
        self.process_collector = ProcessCollector(interval=interval)
        self.file_collector = FileCollector()

    def collect(self):
        events = []

        # collect from process
        events.extend(self.process_collector.collect())

        # collect from file
        events.extend(self.file_collector.collect())

        return events