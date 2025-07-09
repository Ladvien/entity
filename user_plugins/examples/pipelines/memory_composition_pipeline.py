"""Demonstrate composed memory resources using :class:`Workflow`.

Run ``config/dev.yaml`` locally then switch to ``config/prod.yaml`` for
deployment. The same workflow works in both places, highlighting the
dev-to-prod pattern.
"""

from __future__ import annotations

import asyncio
import os
from typing import List

from ..utilities import enable_plugins_namespace

enable_plugins_namespace()
from entity_config.environment import load_env
from pipeline import PipelineStage, PromptPlugin
from pipeline.pipeline import Pipeline, Workflow
from entity.core.builder import AgentBuilder
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
        await memory.save_conversation(context.pipeline_id, context.conversation())
        context.say("Conversation stored")


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


async def main() -> None:
    load_env()
    builder = AgentBuilder()
    database = SQLiteDatabaseResource({"path": "./agent.db"})
    vector_store = create_vector_store()
    memory = Memory(database=database, vector_store=vector_store)
    await builder.resource_registry.add("memory", memory)
    builder.add_plugin(StorePrompt())

    runtime = builder.build_runtime()
    workflow = Workflow({PipelineStage.THINK: ["StorePrompt"]})
    pipeline = Pipeline(approach=workflow)
    result = await pipeline.run_message("remember this", runtime.capabilities)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
