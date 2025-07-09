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
from pipeline import PipelineStage, PromptPlugin, ResourcePlugin  # noqa: E402
from pipeline.config import ConfigLoader
from pipeline.context import PluginContext  # noqa: E402
from plugins.builtin.resources.pg_vector_store import PgVectorStore  # noqa: E402
from plugins.builtin.resources.postgres import PostgresResource  # noqa: E402
from user_plugins.llm.unified import UnifiedLLMResource  # noqa: E402


class VectorMemoryResource(ResourcePlugin):
    """In-memory vector store."""

    stages = [PipelineStage.PARSE]
    name = "vector_memory"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self.vectors: Dict[str, List[float]] = {}

    async def _execute_impl(self, context: PluginContext) -> None:
        return None

    def add(self, key: str, vector: List[float]) -> None:
        self.vectors[key] = vector

    def get(self, key: str) -> List[float] | None:
        return self.vectors.get(key)


class ComplexPrompt(PromptPlugin):
    """Example prompt using the vector memory."""

    dependencies = ["database", "llm", "vector_memory"]
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context: PluginContext) -> None:
        memory: VectorMemoryResource = context.get_resource("vector_memory")
        memory.add("greeting", [1.0, 0.0, 0.0])
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


def main() -> None:
    load_env()
    agent = Agent()
    resources = agent.builder.resource_registry
    db_cls, db_cfg = create_database_config()
    llm_cls, llm_cfg = create_llm_config()
    resources.register("database", db_cls, db_cfg)
    resources.register("llm", llm_cls, llm_cfg)
    resources.register("vector_memory", VectorMemoryResource, {})
    agent.builder.plugin_registry.register_plugin_for_stage(
        ComplexPrompt(), PipelineStage.THINK
    )

    async def run() -> None:
        await resources.build_all()
        print(await agent.handle("hello"))

    asyncio.run(run())


if __name__ == "__main__":
    main()
