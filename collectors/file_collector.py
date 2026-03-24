class FileCollector:
    """Placeholder collector kept for backward compatibility.

    This prototype intentionally focuses on process telemetry and uses only
    Python stdlib + psutil for runtime dependencies.
    """

    def __init__(self, path="."):
        self.path = path

    def start(self):
        return None

    def stop(self):
        return None

    def collect(self):
        return []