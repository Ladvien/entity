"""Run a pipeline with vector memory support.

Usage:
    python -m examples.pipelines.vector_memory_pipeline

Run with the ``-m`` flag or install the package in editable mode.
"""

from __future__ import annotations

import asyncio
import os
from typing import Dict, List, Tuple

from ..utilities import enable_plugins_namespace

enable_plugins_namespace()
from entity_config.environment import load_env
from pipeline import Agent  # noqa: E402
from pipeline import PipelineStage, PromptPlugin  # noqa: E402
from pipeline.config import ConfigLoader
from pipeline.context import PluginContext  # noqa: E402
from plugins.builtin.resources.pg_vector_store import PgVectorStore  # noqa: E402
from plugins.builtin.resources.postgres import PostgresResource  # noqa: E402
from plugins.builtin.resources.duckdb_database import (
    DuckDBDatabaseResource,
)  # noqa: E402
from plugins.builtin.resources.duckdb_vector_store import (
    DuckDBVectorStore,
)  # noqa: E402
from pipeline.resources.memory import Memory
from user_plugins.llm.unified import UnifiedLLMResource  # noqa: E402


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


def main() -> None:
    load_env()
    agent = Agent()
    resources = agent.builder.resource_registry
    db_cls, db_cfg = create_database_config()
    llm_cls, llm_cfg = create_llm_config()
    resources.register("database", db_cls, db_cfg)
    resources.register("llm", llm_cls, llm_cfg)
    vector_store = create_vector_store()
    resources.add("vector_store", vector_store)
    resources.register("memory", Memory, {})
    agent.builder.plugin_registry.register_plugin_for_stage(
        ComplexPrompt(), PipelineStage.THINK
    )

    async def run() -> None:
        await resources.build_all()
        print(await agent.handle("hello"))

    asyncio.run(run())


if __name__ == "__main__":
    main()
