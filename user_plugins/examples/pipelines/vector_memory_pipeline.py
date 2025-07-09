"""Run a pipeline with vector memory support using the Workflow pattern.

Switch between ``config/dev.yaml`` and ``config/prod.yaml`` to apply the
same workflow in different environments.
"""

from __future__ import annotations

import asyncio
import os
from typing import Dict, List, Tuple

from ..utilities import enable_plugins_namespace

enable_plugins_namespace()
from entity_config.environment import load_env
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
from plugins.builtin.resources.duckdb_database import DuckDBDatabaseResource
from plugins.builtin.resources.duckdb_vector_store import DuckDBVectorStore
from entity.resources.memory import Memory
from user_plugins.llm.unified import UnifiedLLMResource


class ComplexPrompt(PromptPlugin):
    """Example prompt using the vector store."""

    dependencies = ["database", "llm", "memory"]
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context: PluginContext) -> None:
        memory: Memory = context.get_resource("memory")
        if memory.vector_store:
            await memory.vector_store.add_embedding("greeting")
            similar = await memory.search_similar("greeting", 1)
            context.add_conversation_entry(
                f"Similar entries: {similar}", role="assistant"
            )
        llm = context.get_llm()
        response = await llm.generate("Respond to the user using stored context.")
        context.add_conversation_entry(response, role="assistant")


def create_database_config() -> Tuple[type, Dict]:
    """Return database class and config based on environment variables."""

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
        }
        return PostgresResource, cfg
    return DuckDBDatabaseResource, {
        "path": "./agent.duckdb",
        "history_table": "history",
    }


def create_llm_config() -> Tuple[type, Dict]:
    """Return LLM class and configuration."""

    base_url = os.getenv("OLLAMA_BASE_URL")
    model = os.getenv("OLLAMA_MODEL")
    if base_url and model:
        cfg = {"provider": "ollama", "base_url": base_url, "model": model}
    else:
        cfg = {"provider": "echo"}
    return UnifiedLLMResource, cfg


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
            "table": "vectors",
        }
        db = PostgresResource(ConfigLoader.from_dict(cfg))
        return PgVectorStore(ConfigLoader.from_dict({"table": "vectors"}), db)
    return DuckDBVectorStore({"table": "vectors", "dimensions": 3})


async def build_registries(workflow: dict[PipelineStage, List]) -> SystemRegistries:
    load_env()
    plugins = PluginRegistry()
    resources = ResourceContainer()
    tools = ToolRegistry()

    db_cls, db_cfg = create_database_config()
    llm_cls, llm_cfg = create_llm_config()
    resources.register("database", db_cls, db_cfg)
    resources.register("llm", llm_cls, llm_cfg)
    resources.add("vector_store", create_vector_store())
    resources.register("memory", Memory, {})

    for stage, stage_plugins in workflow.items():
        for plugin in stage_plugins:
            await plugins.register_plugin_for_stage(plugin, stage)

    await resources.build_all()
    return SystemRegistries(resources=resources, tools=tools, plugins=plugins)


async def main() -> None:
    workflow = {PipelineStage.THINK: [ComplexPrompt()]}
    registries = await build_registries(workflow)
    result = await execute_pipeline("hello", registries)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
