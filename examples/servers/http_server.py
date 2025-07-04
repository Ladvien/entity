"""Run a simple HTTP server using the Entity framework."""

from __future__ import annotations

import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "src"))


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

import asyncio
from typing import Any

from pipeline import ConversationManager, PipelineManager
from pipeline.adapters.http import HTTPAdapter, MessageRequest
from pipeline.initializer import SystemInitializer


async def main() -> None:
    initializer = SystemInitializer.from_yaml("config/dev.yaml")
    registries = await initializer.initialize()
    pipeline_manager = PipelineManager(registries)
    conversation_manager = ConversationManager(registries, pipeline_manager)
    adapter = HTTPAdapter(pipeline_manager, {"host": "127.0.0.1", "port": 8000})

    @adapter.app.post("/conversation")
    async def conversation(req: MessageRequest) -> dict[str, Any]:
        return await conversation_manager.process_request(req.message)

    await adapter.serve(registries)


if __name__ == "__main__":
    asyncio.run(main())
