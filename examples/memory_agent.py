import asyncio
from entity.core.event_loop import EventLoop
from entity.core.context import EventContext
from entity.types.enums import PluginStage
from entity.plugins.base import BasePlugin
from entity.plugins.resource.postgres import PostgresResourcePlugin
from entity.types.context_models import ResourceRegistry


class EchoPlugin(BasePlugin):
    async def handle(self, context: EventContext):
        context.response = f"Echo: {context.request['message']}"


class CheckDataAccessPlugin(BasePlugin):
    async def handle(self, context: EventContext):
        db = context.resources.get("data")
        if db is None:
            context.response = "❌ No DB connection"
            return

        async with db.acquire() as conn:
            version = await conn.fetchval("SELECT version();")
            context.response = f"✅ PostgreSQL version: {version}"


class DemoPluginGraph:
    def __init__(self):
        self.stages = {
            PluginStage.INPUT: [EchoPlugin()],
            PluginStage.TOOL: [CheckDataAccessPlugin()],
        }


async def main():
    # Step 1: Initialize Resource Plugins
    postgres = PostgresResourcePlugin()
    db_pool = await postgres.initialize(
        {
            "username": "postgres",
            "password": "password",
            "name": "memory",
            "host": "localhost",
        }
    )

    # Step 2: Register resources
    resources = ResourceRegistry()
    resources.register("data", db_pool)

    # Step 3: Run the event loop
    loop = EventLoop(plugin_graph=DemoPluginGraph(), resource_registry=resources)
    result = await loop.handle_request({"message": "check database access"})
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
