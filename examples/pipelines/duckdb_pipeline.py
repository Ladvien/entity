"""DuckDB memory pipeline example.

Run with ``python -m examples.pipelines.duckdb_pipeline`` or install the package
in editable mode.
"""

from __future__ import annotations

import asyncio
from typing import Any

from ..utilities import enable_plugins_namespace

enable_plugins_namespace()

from pipeline import Agent, PipelineStage, PromptPlugin
from pipeline.context import PluginContext
from pipeline.resources.memory import Memory
from user_plugins.resources import DuckDBDatabaseResource, DuckDBVectorStore


class SimilarityPrompt(PromptPlugin):
    """Store conversation and show similar messages."""

    dependencies = ["memory"]
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, ctx: PluginContext) -> None:
        memory: Memory = ctx.get_resource("memory")
        await memory.save_conversation(ctx.pipeline_id, ctx.get_conversation_history())
        if memory.vector_store:
            await memory.vector_store.add_embedding(ctx.message)
            similar = await memory.search_similar(ctx.message, 1)
            ctx.add_conversation_entry(f"Similar entries: {similar}", role="assistant")


def main() -> None:
    agent = Agent()
    resources = agent.builder.resource_registry

    resources.register(
        "database",
        DuckDBDatabaseResource,
        {"path": "./agent.duckdb", "history_table": "history"},
    )
    resources.register(
        "vector_store",
        DuckDBVectorStore,
        {"table": "vectors", "dimensions": 3},
    )
    resources.register("memory", Memory, {})
    agent.builder.plugin_registry.register_plugin_for_stage(
        SimilarityPrompt(), PipelineStage.THINK
    )

    async def run() -> None:
        await resources.build_all()
        print(await agent.handle("hello world"))

    asyncio.run(run())


if __name__ == "__main__":
    main()
