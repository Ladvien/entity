"""Demonstrate composed memory resource using SQLite, PGVector and local files."""

from __future__ import annotations

import asyncio
import os
import pathlib
import sys

# Ensure project source is available for imports
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "src"))  # noqa: E402

from ..utilities import enable_plugins_namespace

enable_plugins_namespace()

from plugins.builtin.resources.postgres import PostgresResource
from plugins.builtin.resources.pg_vector_store import PgVectorStore
from plugins.builtin.resources.sqlite_storage import (
    SQLiteStorageResource as SQLiteDatabaseResource,
)
from user_plugins.resources import DuckDBVectorStore
from user_plugins.memory_resource import MemoryResource

from entity import Agent  # noqa: E402
from pipeline import PipelineStage, PromptPlugin  # noqa: E402
from pipeline.config import ConfigLoader
from pipeline.context import PluginContext  # noqa: E402


class StorePrompt(PromptPlugin):
    """Example prompt that persists conversation history."""

    dependencies = ["memory"]
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context: PluginContext) -> None:
        memory: MemoryResource = context.get_resource("memory")
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
    memory = MemoryResource(database=database, vector_store=vector_store)

    agent.builder.resource_registry.add("memory", memory)
    agent.builder.plugin_registry.register_plugin_for_stage(
        StorePrompt(), PipelineStage.THINK
    )

    async def run() -> None:
        print(await agent.handle("remember this"))

    asyncio.run(run())


if __name__ == "__main__":
    main()
