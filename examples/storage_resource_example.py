"""Demonstrate StorageResource with SQLite and local files.

Run with ``python -m examples.storage_resource_example`` or install the package
in editable mode.
"""

from __future__ import annotations

import asyncio
from datetime import datetime

from .utilities import enable_plugins_namespace

enable_plugins_namespace()

from pipeline import Agent, PipelineStage, PromptPlugin
from pipeline.context import ConversationEntry, PluginContext
from pipeline.resources.memory import Memory
from plugins.builtin.resources.local_filesystem import LocalFileSystemResource
from plugins.builtin.resources.sqlite_storage import (
    SQLiteStorageResource as SQLiteDatabaseResource,
)
from plugins.builtin.resources.storage_resource import StorageResource


class StorePrompt(PromptPlugin):
    """Store message history and save the input to a file."""

    dependencies = ["memory", "storage"]
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, ctx: PluginContext) -> None:
        memory: Memory = ctx.get_resource("memory")
        storage: StorageResource = ctx.get_resource("storage")
        await memory.save_conversation(ctx.pipeline_id, ctx.get_conversation_history())
        path = await storage.store_file("input.txt", ctx.message.encode())
        ctx.add_conversation_entry(f"File stored at {path}", role="assistant")


def main() -> None:
    agent = Agent()

    database = SQLiteDatabaseResource({"path": "./agent.db"})
    filesystem = LocalFileSystemResource({"base_path": "./files"})

    memory = Memory(database=database)
    storage = StorageResource(filesystem=filesystem)

    agent.builder.resource_registry.add("memory", memory)
    agent.builder.resource_registry.add("storage", storage)
    agent.builder.plugin_registry.register_plugin_for_stage(
        StorePrompt(), PipelineStage.THINK
    )

    async def run() -> None:
        print(await agent.handle("remember this"))

    asyncio.run(run())


if __name__ == "__main__":
    main()
