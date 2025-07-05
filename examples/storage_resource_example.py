"""Demonstrate StorageResource with SQLite and local files."""

from __future__ import annotations

import asyncio
import pathlib
import sys
from datetime import datetime

# Make the repository's ``src`` directory importable
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from utilities import enable_plugins_namespace

enable_plugins_namespace()

from plugins.builtin.resources.local_filesystem import LocalFileSystemResource
from plugins.builtin.resources.sqlite_storage import (
    SQLiteStorageResource as SQLiteDatabaseResource,
)
from plugins.builtin.resources.storage_resource import StorageResource
from pipeline.context import PluginContext, ConversationEntry
from pipeline import PipelineStage, PromptPlugin
from entity import Agent


class StorePrompt(PromptPlugin):
    """Store message history and save the input to a file."""

    dependencies = ["storage"]
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, ctx: PluginContext) -> None:
        storage: StorageResource = ctx.get_resource("storage")
        await storage.save_history(ctx.pipeline_id, ctx.get_conversation_history())
        path = await storage.store_file("input.txt", ctx.message.encode())
        ctx.add_conversation_entry(f"File stored at {path}", role="assistant")


def main() -> None:
    agent = Agent()

    database = SQLiteDatabaseResource({"path": "./agent.db"})
    filesystem = LocalFileSystemResource({"base_path": "./files"})
    storage = StorageResource(database=database, filesystem=filesystem)

    agent.builder.resource_registry.add("storage", storage)
    agent.builder.plugin_registry.register_plugin_for_stage(
        StorePrompt(), PipelineStage.THINK
    )

    async def run() -> None:
        print(await agent.handle("remember this"))

    asyncio.run(run())


if __name__ == "__main__":
    main()
