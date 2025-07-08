"""Demonstrate runtime configuration reload using the CLI."""

from __future__ import annotations

import pathlib
import sys
import tempfile

import yaml

# Allow importing from the repository's src directory
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))

# Expose local plugins namespace
from .utilities import enable_plugins_namespace

enable_plugins_namespace()

# Make this module importable as "examples.config_reload_example" even when executed directly
sys.modules.setdefault("examples.config_reload_example", sys.modules[__name__])

from cli import CLI
from pipeline import Agent
from pipeline.base_plugins import PromptPlugin
from pipeline.context import PluginContext
from pipeline.stages import PipelineStage


class GreetingPrompt(PromptPlugin):
    """Simple prompt plugin that prints a greeting."""

    stages = [PipelineStage.THINK]
    name = "greeting"

    async def _execute_impl(
        self, context: PluginContext
    ) -> None:  # pragma: no cover - example
        message = self.config.get("message", "Hello")
        print(f"GreetingPrompt: {message}")


async def main() -> None:
    base_config = pathlib.Path("config/dev.yaml")
    agent = Agent(str(base_config))

    def list_think_plugins() -> list[str]:
        reg = agent.builder.plugin_registry
        return [
            reg.get_plugin_name(p)
            for p in reg.get_plugins_for_stage(PipelineStage.THINK)
        ]

    print("THINK plugins before reload:", list_think_plugins())

    updated = tempfile.NamedTemporaryFile(delete=False, suffix=".yaml")
    updated_cfg = {
        "plugins": {
            "prompts": {
                "greeting": {
                    "type": "examples.config_reload_example:GreetingPrompt",
                    "message": "Hi from the updated config!",
                }
            }
        }
    }
    updated.write(yaml.dump(updated_cfg).encode())
    updated.close()

    cli = CLI.__new__(CLI)
    result = cli._reload_config(agent, updated.name)
    print("Reload exit code:", result)

    print("THINK plugins after reload:", list_think_plugins())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
