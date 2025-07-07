"""Run a pipeline with vector memory support.

Usage:
    python examples/vector_memory_pipeline.py
"""

from __future__ import annotations

import asyncio
import os
import pathlib
import sys
from typing import Dict, List

# Ensure project source is available for imports
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "src"))  # noqa: E402

from ..utilities import enable_plugins_namespace

enable_plugins_namespace()
from user_plugins.llm.unified import UnifiedLLMResource  # noqa: E402
from plugins.builtin.resources.pg_vector_store import PgVectorStore  # noqa: E402
from plugins.builtin.resources.postgres import PostgresResource  # noqa: E402

from entity_config.environment import load_env
from entity import Agent  # noqa: E402
from pipeline import PipelineStage, PromptPlugin, ResourcePlugin  # noqa: E402
from pipeline.config import ConfigLoader
from pipeline.context import PluginContext  # noqa: E402


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


def create_database() -> PostgresResource | DuckDBDatabaseResource:
    """Return a database resource based on environment variables."""

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
        return PostgresResource(ConfigLoader.from_dict(cfg))
    return DuckDBDatabaseResource(
        {"path": "./agent.duckdb", "history_table": "history"}
    )


def create_llm() -> UnifiedLLMResource:
    """Return a configured LLM resource."""

    base_url = os.getenv("OLLAMA_BASE_URL")
    model = os.getenv("OLLAMA_MODEL")
    if base_url and model:
        cfg = {"provider": "ollama", "base_url": base_url, "model": model}
    else:
        cfg = {"provider": "echo"}
    return UnifiedLLMResource(ConfigLoader.from_dict(cfg))


def main() -> None:
    load_env()
    agent = Agent()
    agent.builder.resource_registry.add("database", create_database())
    agent.builder.resource_registry.add("llm", create_llm())
    agent.builder.resource_registry.add("vector_memory", VectorMemoryResource())
    agent.builder.plugin_registry.register_plugin_for_stage(
        ComplexPrompt(), PipelineStage.THINK
    )

    async def run() -> None:
        print(await agent.handle("hello"))

    asyncio.run(run())


if __name__ == "__main__":
    main()
