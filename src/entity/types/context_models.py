from typing import Dict, Any


class ResourceRegistry:
    def __init__(self):
        self._resources: Dict[str, Any] = {}

    def register(self, name: str, instance: Any):
        self._resources[name] = instance

    def get(self, name: str):
        return self._resources.get(name)
