"""Demonstrate composed memory resource using SQLite, PGVector and local files."""

from __future__ import annotations

import asyncio
import pathlib
import sys

# Ensure project source is available for imports
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "src"))  # noqa: E402

from entity import Agent  # noqa: E402
from pipeline import PipelineStage, PromptPlugin  # noqa: E402
from pipeline.context import PluginContext  # noqa: E402
from pipeline.plugins.resources.local_filesystem import (  # noqa: E402
    LocalFileSystemResource,
)
from pipeline.plugins.resources.memory import MemoryResource  # noqa: E402
from pipeline.plugins.resources.pg_vector_store import PgVectorStore  # noqa: E402
from pipeline.plugins.resources.sqlite_storage import (  # noqa: E402
    SQLiteStorageResource as SQLiteDatabaseResource,
)


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


def main() -> None:
    agent = Agent()

    database = SQLiteDatabaseResource({"path": "./agent.db"})
    vector_store = PgVectorStore({"table": "embeddings"})
    filesystem = LocalFileSystemResource({"base_path": "./files"})

    memory = MemoryResource(
        database=database,
        vector_store=vector_store,
        filesystem=filesystem,
    )

    agent.resource_registry.add("memory", memory)
    agent.plugin_registry.register_plugin_for_stage(StorePrompt(), PipelineStage.THINK)

    async def run() -> None:
        print(await agent.handle("remember this"))

    asyncio.run(run())


if __name__ == "__main__":
    main()
