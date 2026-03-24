# core/monitor.py

from collectors.process_collector import ProcessCollector
from collectors.file_collector import FileCollector
from collectors.network_collector import NetworkCollector
from collectors.auth_collector import AuthCollector


class Monitor:
    def __init__(self, interval=1):
        self.process_collector = ProcessCollector(interval=interval)
        self.file_collector = FileCollector()
        self.network_collector = NetworkCollector()
        self.auth_collector = AuthCollector()

    def collect(self):
        events = []

        # collect from process
        events.extend(self.process_collector.collect())

        # collect from file
        events.extend(self.file_collector.collect())

        # collect from network
        events.extend(self.network_collector.collect())

        # collect from authentication
        events.extend(self.auth_collector.collect())

        return events