"""Demonstrate composed memory resource using SQLite, PGVector and local files.

Run with ``python -m examples.pipelines.memory_composition_pipeline`` or install
the package in editable mode.
"""

from __future__ import annotations

import asyncio
import os

from ..utilities import enable_plugins_namespace

enable_plugins_namespace()

from pipeline import Agent  # noqa: E402
from pipeline import PipelineStage, PromptPlugin  # noqa: E402
from pipeline.config import ConfigLoader
from pipeline.context import PluginContext  # noqa: E402
from plugins.builtin.resources.pg_vector_store import PgVectorStore
from plugins.builtin.resources.postgres import PostgresResource
from plugins.builtin.resources.sqlite_storage import (
    SQLiteStorageResource as SQLiteDatabaseResource,
)
from entity.resources.memory import Memory
from user_plugins.resources import DuckDBVectorStore


class StorePrompt(PromptPlugin):
    """Example prompt that persists conversation history."""

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


def main() -> None:
    agent = Agent()

    database = SQLiteDatabaseResource({"path": "./agent.db"})
    vector_store = create_vector_store()
    memory = Memory(database=database, vector_store=vector_store)

    agent.builder.resource_registry.add("memory", memory)
    agent.builder.plugin_registry.register_plugin_for_stage(
        StorePrompt(), PipelineStage.THINK
    )

    async def run() -> None:
        print(await agent.handle("remember this"))

    asyncio.run(run())


if __name__ == "__main__":
    main()
