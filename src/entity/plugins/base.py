from abc import ABC, abstractmethod


class BasePlugin(ABC):
    @abstractmethod
    async def handle(self, context):
        pass
