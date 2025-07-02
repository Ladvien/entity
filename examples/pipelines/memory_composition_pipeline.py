"""Demonstrate composed memory resource using SQLite, PGVector and local files."""

from __future__ import annotations

import asyncio
import pathlib
import sys
from typing import Dict, List

# Ensure project source is available for imports
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "src"))  # noqa: E402

from entity import Agent  # noqa: E402
from pipeline import PipelineStage, PromptPlugin  # noqa: E402
from pipeline.context import PluginContext  # noqa: E402
from pipeline.plugins.resources.memory import MemoryResource  # noqa: E402
from pipeline.plugins.resources.pg_vector_store import PgVectorStore  # noqa: E402
from pipeline.plugins.resources.sqlite_storage import (
    SQLiteStorageResource as SQLiteDatabaseResource,
)  # noqa: E402
from pipeline.resources.filesystem import FileSystemResource  # noqa: E402


class DummyFileSystem(FileSystemResource):
    """Minimal filesystem backend that prints actions."""

    async def store(self, key: str, content: bytes) -> str:
        path = f"/tmp/{key}"
        print(f"Storing {len(content)} bytes at {path}")
        return path

    async def load(self, key: str) -> bytes:
        print(f"Loading content for {key}")
        return b""


class StorePrompt(PromptPlugin):
    """Example prompt that persists conversation history."""

    dependencies = ["memory"]
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context: PluginContext) -> None:
        memory: MemoryResource = context.get_resource("memory")
        await memory.save_conversation(
            context.pipeline_id, context.get_conversation_history()
        )
        context.add_conversation_entry("Conversation stored", role="assistant")


def main() -> None:
    agent = Agent()

    database = SQLiteDatabaseResource({"path": "./agent.db"})
    vector_store = PgVectorStore({"table": "embeddings"})
    filesystem = DummyFileSystem()

    memory = MemoryResource(
        database=database,
        vector_store=vector_store,
        filesystem=filesystem,
    )

    agent.resource_registry.add("memory", memory)
    agent.plugin_registry.register_plugin_for_stage(StorePrompt(), PipelineStage.THINK)

    async def run() -> None:
        print(await agent.handle("remember this"))

    asyncio.run(run())


if __name__ == "__main__":
    main()
