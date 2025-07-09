"""DuckDB memory pipeline using a Workflow object.

Change ``config/dev.yaml`` to ``config/prod.yaml`` for production. This
commented switch showcases the hybrid dev/prod pattern.
"""

from __future__ import annotations

import asyncio
from typing import List

from ..utilities import enable_plugins_namespace

enable_plugins_namespace()
from entity.config.environment import load_env
from pipeline import (
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    ResourceContainer,
    SystemRegistries,
    ToolRegistry,
    execute_pipeline,
)
from entity.core.context import PluginContext
from entity.resources.memory import Memory
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


async def build_registries(workflow: dict[PipelineStage, List]) -> SystemRegistries:
    load_env()
    plugins = PluginRegistry()
    resources = ResourceContainer()
    tools = ToolRegistry()

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

    for stage, stage_plugins in workflow.items():
        for plugin in stage_plugins:
            await plugins.register_plugin_for_stage(plugin, stage)

    await resources.build_all()
    return SystemRegistries(resources=resources, tools=tools, plugins=plugins)


async def main() -> None:
    workflow = {PipelineStage.THINK: [SimilarityPrompt()]}
    registries = await build_registries(workflow)
    result = await execute_pipeline("hello world", registries)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
