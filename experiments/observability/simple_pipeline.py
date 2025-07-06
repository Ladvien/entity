from __future__ import annotations

"""Minimal pipeline emitting Prometheus metrics and OpenTelemetry traces."""

import asyncio
from typing import Any, Dict

from pipeline import (
    PluginRegistry,
    PromptPlugin,
    ResourceContainer,
    SystemRegistries,
    ToolPlugin,
    ToolRegistry,
    execute_pipeline,
)
from pipeline.logging import configure_logging
from pipeline.observability import start_metrics_server, start_span
from pipeline.stages import PipelineStage


class GreeterPrompt(PromptPlugin):
    """Create a greeting based on the incoming message."""

    stages = [PipelineStage.DO]
    name = "greeter_prompt"

    async def _execute_impl(self, context) -> None:
        message = context.message
        context.set_response(f"Hello, {message}")


class UpperTool(ToolPlugin):
    """Return an upper-case version of ``text``."""

    stages = [PipelineStage.DO]
    name = "upper_tool"

    async def execute_function(self, params: Dict[str, Any]) -> str:
        return str(params.get("text", "")).upper()

    async def execute(self, params: Dict[str, Any]) -> str:
        return await self.execute_function_with_retry(params)


def build_registries() -> SystemRegistries:
    plugins = PluginRegistry()
    resources = ResourceContainer()
    tools = ToolRegistry()

    plugins.register_plugin_for_stage(GreeterPrompt(), PipelineStage.DO)
    tools.add("upper", UpperTool())

    return SystemRegistries(resources=resources, tools=tools, plugins=plugins)


async def main() -> None:
    configure_logging(level="INFO")
    start_metrics_server(port=9001)

    registries = build_registries()
    async with start_span("observability_pipeline"):
        result = await execute_pipeline("world", registries)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
