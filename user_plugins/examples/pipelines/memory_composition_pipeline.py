"""Demonstrate composed memory resources using a simple Workflow.

Swap ``config/dev.yaml`` for ``config/prod.yaml`` to run the same
workflow in production. This illustrates the hybrid dev/prod pattern.
"""

from __future__ import annotations

import asyncio
import os
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
from pipeline.config import ConfigLoader
from entity.core.context import PluginContext
from plugins.builtin.resources.pg_vector_store import PgVectorStore
from plugins.builtin.resources.postgres import PostgresResource
from plugins.builtin.resources.sqlite_storage import (
    SQLiteStorageResource as SQLiteDatabaseResource,
)
from entity.resources.memory import Memory
from user_plugins.resources import DuckDBVectorStore


class StorePrompt(PromptPlugin):
    """Persist conversation history."""

    dependencies = ["memory"]
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context: PluginContext) -> None:
        memory: Memory = context.get_resource("memory")
        await memory.save_conversation(
            context.pipeline_id, context.get_conversation_history()
        )
        context.add_conversation_entry("Conversation stored", role="assistant")


def create_vector_store() -> PgVectorStore | DuckDBVectorStore:
    """Return a vector store based on environment variables."""

    host = os.getenv("DB_HOST")
    user = os.getenv("DB_USERNAME")
    password = os.getenv("DB_PASSWORD")
    if host and user:
        cfg = {
            "host": host,
            "port": 5432,
            "name": user,
            "username": user,
            "password": password or "",
            "table": "embeddings",
        }
        db = PostgresResource(ConfigLoader.from_dict(cfg))
        return PgVectorStore(ConfigLoader.from_dict({"table": "embeddings"}), db)
    return DuckDBVectorStore({"table": "embeddings"})


async def build_registries(workflow: dict[PipelineStage, List]) -> SystemRegistries:
    load_env()
    plugins = PluginRegistry()
    resources = ResourceContainer()
    tools = ToolRegistry()

    database = SQLiteDatabaseResource({"path": "./agent.db"})
    vector_store = create_vector_store()
    memory = Memory(database=database, vector_store=vector_store)
    resources.add("memory", memory)

    for stage, stage_plugins in workflow.items():
        for plugin in stage_plugins:
            await plugins.register_plugin_for_stage(plugin, stage)

    return SystemRegistries(resources=resources, tools=tools, plugins=plugins)


async def main() -> None:
    workflow = {PipelineStage.THINK: [StorePrompt()]}
    registries = await build_registries(workflow)
    result = await execute_pipeline("remember this", registries)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
