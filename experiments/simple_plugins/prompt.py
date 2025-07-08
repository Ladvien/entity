from __future__ import annotations

"""Demonstration prompt plugin, not production ready."""

from typing import Awaitable, Callable

from pipeline.base_plugins import PromptPlugin
from pipeline.context import PluginContext
from pipeline.stages import PipelineStage

PromptBehavior = Callable[[PluginContext], Awaitable[None]]


async def default_behavior(context: PluginContext) -> None:
    context.set_response("Hello from simple prompt")


class ComposedPrompt(PromptPlugin):
    """Prompt plugin composed with a behavior callable."""

    stages = [PipelineStage.THINK]
    name = "composed_prompt"

    def __init__(
        self, behavior: PromptBehavior | None = None, config: dict | None = None
    ) -> None:
        super().__init__(config)
        self._behavior = behavior or default_behavior

    async def _execute_impl(self, context: PluginContext) -> None:
        await self._behavior(context)
