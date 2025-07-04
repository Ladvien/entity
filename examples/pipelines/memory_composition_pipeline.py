"""Demonstrate composed memory resource using SQLite, PGVector and local files."""

from __future__ import annotations

import asyncio
import pathlib
import sys

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
from pipeline import PipelineStage, PromptPlugin  # noqa: E402
from pipeline.context import PluginContext  # noqa: E402
<<<<<<< HEAD
from pipeline.resources.memory_resource import MemoryResource  # noqa: E402
from plugins.resources.local_filesystem import LocalFileSystemResource  # noqa: E402
from plugins.resources.pg_vector_store import PgVectorStore  # noqa: E402
from plugins.resources.sqlite_storage import (
=======
from user_plugins.local_filesystem import (
    LocalFileSystemResource,
)  # noqa: E402
from user_plugins.memory_resource import MemoryResource  # noqa: E402
from user_plugins.pg_vector_store import PgVectorStore  # noqa: E402
from user_plugins.sqlite_storage import (
>>>>>>> af319b68dc2109eede14ae624413f7e5304d62df
    SQLiteStorageResource as SQLiteDatabaseResource,
)  # noqa: E402


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

    agent.builder.resource_registry.add("memory", memory)
    agent.builder.plugin_registry.register_plugin_for_stage(
        StorePrompt(), PipelineStage.THINK
    )

    async def run() -> None:
        print(await agent.handle("remember this"))

    asyncio.run(run())


if __name__ == "__main__":
    main()
