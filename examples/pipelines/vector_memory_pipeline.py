"""Run a pipeline with vector memory support.

Usage:
    python examples/vector_memory_pipeline.py
"""

from __future__ import annotations

import asyncio
import pathlib
import sys
from typing import Dict, List

# Ensure project source is available for imports
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "src"))  # noqa: E402

from entity import Agent  # noqa: E402
from pipeline import PipelineStage, PromptPlugin, ResourcePlugin  # noqa: E402
from pipeline.context import PluginContext  # noqa: E402
<<<<<<< HEAD
from pipeline.plugins.resources.llm.unified import \
    UnifiedLLMResource  # noqa: E402
from pipeline.plugins.resources.pg_vector_store import \
    PgVectorStore  # noqa: E402
from pipeline.plugins.resources.postgres import PostgresResource  # noqa: E402
=======
from pipeline.resources.llm.unified import UnifiedLLMResource  # noqa: E402
from pipeline.resources.pg_vector_store import PgVectorStore  # noqa: E402
from pipeline.resources.postgres_database import (
    PostgresDatabaseResource,
)  # noqa: E402
>>>>>>> 31c26c6f08f011fda24b488de4c679ad0b2325fd


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


def main() -> None:
    agent = Agent()
    agent.resource_registry.add(
        "database",
        PostgresResource(
            {
                "host": "localhost",
                "port": 5432,
                "name": "dev_db",
                "username": "agent",
                "password": "",
            }
        ),
    )
    agent.resource_registry.add("llm", UnifiedLLMResource({"provider": "echo"}))
    agent.resource_registry.add("vector_memory", VectorMemoryResource())
    agent.plugin_registry.register_plugin_for_stage(
        ComplexPrompt(), PipelineStage.THINK
    )

    async def run() -> None:
        print(await agent.handle("hello"))

    asyncio.run(run())


if __name__ == "__main__":
    main()
