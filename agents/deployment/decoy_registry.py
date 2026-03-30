# agents/deployment/decoy_registry.py

class DecoyRegistry:
    def __init__(self):
        self._registry = {}

    def add(self, path, metadata):
        self._registry[path] = metadata

    def get(self, path):
        return self._registry.get(path)

    def exists(self, path):
        return path in self._registry

    def get_all(self):
        return self._registry