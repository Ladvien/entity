"""DuckDB memory pipeline example."""

from __future__ import annotations

import asyncio
import pathlib
import sys
from typing import Any

# Ensure project source is available for imports
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "src"))

from utilities import enable_plugins_namespace

enable_plugins_namespace()

from user_plugins.duckdb_database import DuckDBDatabaseResource
from user_plugins.duckdb_vector_store import DuckDBVectorStore
from user_plugins.memory_resource import MemoryResource

from entity import Agent
from pipeline import PipelineStage, PromptPlugin
from pipeline.context import PluginContext


class SimilarityPrompt(PromptPlugin):
    """Store conversation and show similar messages."""

    dependencies = ["memory"]
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, ctx: PluginContext) -> None:
        memory: MemoryResource = ctx.get_resource("memory")
        await memory.save_conversation(ctx.pipeline_id, ctx.get_conversation_history())
        if memory.vector_store:
            await memory.vector_store.add_embedding(ctx.message)
            similar = await memory.search_similar(ctx.message, 1)
            ctx.add_conversation_entry(f"Similar entries: {similar}", role="assistant")


def main() -> None:
    agent = Agent()

    database = DuckDBDatabaseResource(
        {"path": "./agent.duckdb", "history_table": "history"}
    )
    vector_store = DuckDBVectorStore({"table": "vectors", "dimensions": 3}, database)
    memory = MemoryResource(database=database, vector_store=vector_store)

    agent.builder.resource_registry.add("memory", memory)
    agent.builder.plugin_registry.register_plugin_for_stage(
        SimilarityPrompt(), PipelineStage.THINK
    )

    async def run() -> None:
        print(await agent.handle("hello world"))

    asyncio.run(run())


if __name__ == "__main__":
    main()
