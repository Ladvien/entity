"""Run a pipeline with vector memory support using :class:`Workflow`.

Start with ``config/dev.yaml`` for local testing and deploy with
``config/prod.yaml``. The workflow definition stays the same across
environments.
"""

from __future__ import annotations

import asyncio
import os
from typing import Dict, List, Tuple

from ..utilities import enable_plugins_namespace

enable_plugins_namespace()
from entity.config.environment import load_env
from pipeline import PipelineStage, PromptPlugin  # noqa: E402
from pipeline.pipeline import Pipeline, Workflow
from entity.core.builder import AgentBuilder
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
            context.say(f"Similar entries: {similar}")
        llm = context.get_llm()
        response = await llm.generate("Respond to the user using stored context.")
        context.say(response)


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


async def main() -> None:
    load_env()
    builder = AgentBuilder()
    db_cls, db_cfg = create_database_config()
    llm_cls, llm_cfg = create_llm_config()
    builder.resource_registry.register("database", db_cls, db_cfg)
    builder.resource_registry.register("llm", llm_cls, llm_cfg)
    await builder.resource_registry.add("vector_store", create_vector_store())
    builder.resource_registry.register("memory", Memory, {})
    builder.add_plugin(ComplexPrompt())

    runtime = builder.build_runtime()
    workflow = Workflow({PipelineStage.THINK: ["ComplexPrompt"]})
    pipeline = Pipeline(approach=workflow)
    result = await pipeline.run_message("hello", runtime.capabilities)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
