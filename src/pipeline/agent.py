from __future__ import annotations

from typing import Any, Callable, Dict

from .pipeline import SystemRegistries, execute_pipeline
from .plugins import BasePlugin, PluginAutoClassifier
from .registry import PluginRegistry, ResourceRegistry, ToolRegistry
from .stages import PipelineStage


class Agent:
    """Simple agent for registering plugins and executing a pipeline."""

    def __init__(self) -> None:
        self.registries = SystemRegistries(
            resources=ResourceRegistry(), tools=ToolRegistry(), plugins=PluginRegistry()
        )

    # ------------------------------------------------------------------
    def plugin(self, **hints: Any) -> Callable[[Callable], Callable]:
        """Decorator to register a function as a plugin."""

        def decorator(func: Callable) -> Callable:
            plugin = PluginAutoClassifier.classify(func, hints)
            for stage in plugin.stages:
                self.registries.plugins.register_plugin_for_stage(plugin, stage)
            return func

        return decorator

    def add_plugin(self, plugin: BasePlugin) -> None:
        for stage in getattr(plugin, "stages", [PipelineStage.DO]):
            self.registries.plugins.register_plugin_for_stage(plugin, stage)

    async def run_pipeline(self, user_message: str) -> Dict[str, Any]:
        return await execute_pipeline(user_message, self.registries)

    def run(self) -> None:
        raise NotImplementedError("Server functionality is not implemented")
