"""Example demonstrating error handling with BasicLogger and ErrorFormatter."""

from __future__ import annotations

import asyncio
import pathlib
import sys

# Make the repository's ``src`` directory importable
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from .utilities import enable_plugins_namespace

# Expose the local ``plugins`` namespace
enable_plugins_namespace()

from user_plugins.failure import BasicLogger, ErrorFormatter

from entity import Agent
from pipeline import PipelineStage, PromptPlugin
from pipeline.context import PluginContext


class FailingPrompt(PromptPlugin):
    """Prompt that intentionally raises an error."""

    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context: PluginContext) -> None:
        raise RuntimeError("simulated failure")


def main() -> None:
    agent = Agent()
    agent.builder.plugin_registry.register_plugin_for_stage(
        BasicLogger(), PipelineStage.ERROR
    )
    agent.builder.plugin_registry.register_plugin_for_stage(
        ErrorFormatter(), PipelineStage.ERROR
    )
    agent.builder.plugin_registry.register_plugin_for_stage(
        FailingPrompt(), PipelineStage.THINK
    )

    async def run() -> None:
        response = await agent.handle("trigger failure")
        print(response)

    asyncio.run(run())


if __name__ == "__main__":
    main()
