import asyncio
from entity.core.event_loop import EventLoop
from entity.types.enums import PluginStage
from entity.plugins.base import BasePlugin


class EchoPlugin(BasePlugin):
    async def handle(self, context):
        context.response = f"Echo: {context.request['message']}"


class DummyPluginGraph:
    def __init__(self):
        self.stages = {
            PluginStage.INPUT: [EchoPlugin()],
        }


class DummyResourceRegistry:
    def get(self, _):
        return None


async def main():
    loop = EventLoop(
        plugin_graph=DummyPluginGraph(), resource_registry=DummyResourceRegistry()
    )
    result = await loop.handle_request({"message": "hello world"})
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
