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


def _enable_plugins_namespace() -> None:
    import importlib
    import pkgutil
    import types

    import pipeline.user_plugins
    import pipeline.user_plugins.resources as plugin_resources
    import pipeline.resources

    plugins_mod = types.ModuleType("plugins")
    plugins_mod.__dict__.update(vars(pipeline.user_plugins))
    sys.modules["plugins"] = plugins_mod
    sys.modules["user_plugins.resources"] = plugin_resources
    plugins_mod.resources = plugin_resources

    for _, name, _ in pkgutil.walk_packages(
        pipeline.resources.__path__, prefix="pipeline.resources."
    ):
        module = importlib.import_module(name)
        alias = name.replace("pipeline.resources.", "user_plugins.")
        sys.modules[alias] = module
        parent_alias = alias.rsplit(".", 1)[0]
        if parent_alias == "plugins":
            setattr(plugins_mod, alias.split(".")[-1], module)
        else:
            parent = sys.modules.setdefault(
                parent_alias, types.ModuleType(parent_alias)
            )
            setattr(parent, alias.split(".")[-1], module)


_enable_plugins_namespace()

from entity import Agent  # noqa: E402
from pipeline import PipelineStage, PromptPlugin, ResourcePlugin  # noqa: E402
from pipeline.context import PluginContext  # noqa: E402
from config.environment import load_env
from pipeline.config import ConfigLoader
from user_plugins.llm.unified import UnifiedLLMResource  # noqa: E402
from user_plugins.pg_vector_store import PgVectorStore  # noqa: E402
from user_plugins.postgres import PostgresResource  # noqa: E402


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
    load_env()
    agent = Agent()
    agent.builder.resource_registry.add(
        "database",
        PostgresResource(
            ConfigLoader.from_dict(
                {
                    "host": "${DB_HOST}",
                    "port": 5432,
                    "name": "${DB_USERNAME}",
                    "username": "${DB_USERNAME}",
                    "password": "${DB_PASSWORD}",
                }
            )
        ),
    )
    agent.builder.resource_registry.add(
        "llm",
        UnifiedLLMResource(
            ConfigLoader.from_dict(
                {
                    "provider": "ollama",
                    "base_url": "${OLLAMA_BASE_URL}",
                    "model": "${OLLAMA_MODEL}",
                }
            )
        ),
    )
    agent.builder.resource_registry.add("vector_memory", VectorMemoryResource())
    agent.builder.plugin_registry.register_plugin_for_stage(
        ComplexPrompt(), PipelineStage.THINK
    )

    async def run() -> None:
        print(await agent.handle("hello"))

    asyncio.run(run())


if __name__ == "__main__":
    main()
