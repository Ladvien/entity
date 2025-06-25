# src/entity/plugins/resource/base.py
from abc import ABC, abstractmethod


class ResourcePlugin(ABC):
    @abstractmethod
    def get_resource_name(self) -> str:
        pass

    @abstractmethod
    async def initialize(self, config: dict):
        """Should return the actual resource object to be registered."""
        pass
