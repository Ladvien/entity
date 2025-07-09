"""DuckDB memory pipeline using :class:`Workflow`.

Use ``config/dev.yaml`` for local runs and switch to ``config/prod.yaml``
in production. The workflow remains identical, illustrating the
dev-to-prod approach.
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
        await memory.save_conversation(ctx.pipeline_id, ctx.conversation())
        if memory.vector_store:
            await memory.vector_store.add_embedding(ctx.message)
            similar = await memory.search_similar(ctx.message, 1)
            ctx.say(f"Similar entries: {similar}")


async def main() -> None:
    load_env()
    builder = AgentBuilder()
    builder.resource_registry.register(
        "database",
        DuckDBDatabaseResource,
        {"path": "./agent.duckdb", "history_table": "history"},
    )
    builder.resource_registry.register(
        "vector_store",
        DuckDBVectorStore,
        {"table": "vectors", "dimensions": 3},
    )
    builder.resource_registry.register("memory", Memory, {})
    builder.add_plugin(SimilarityPrompt())

    runtime = builder.build_runtime()
    workflow = Workflow({PipelineStage.THINK: ["SimilarityPrompt"]})
    pipeline = Pipeline(approach=workflow)
    result = await pipeline.run_message("hello world", runtime.capabilities)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
