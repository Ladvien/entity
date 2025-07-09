"""Simple pipeline execution example using :class:`Workflow`.

Swap ``config/dev.yaml`` with ``config/prod.yaml`` to run the same
workflow locally and in production. This demonstrates the dev-to-prod
workflow pattern.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

from ..utilities import enable_plugins_namespace

enable_plugins_namespace()
from user_plugins.llm.unified import UnifiedLLMResource

from entity.config.environment import load_env
from pipeline import PipelineStage, PromptPlugin, ToolPlugin
from pipeline.pipeline import Pipeline, Workflow
from entity.core.builder import AgentBuilder


class CalculatorTool(ToolPlugin):
    """Evaluate a math expression safely."""

    stages = [PipelineStage.DO]
    name = "calculator"

    async def execute_function(self, params: Dict[str, Any]) -> Any:  # pragma: no cover
        expression = params.get("expression")
        if expression is None:
            raise ValueError("'expression' parameter is required")
        allowed_names: dict[str, dict[str, object]] = {"__builtins__": {}}
        try:
            return eval(str(expression), allowed_names, {})
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"Invalid expression: {exc}") from exc

    async def execute(self, params: Dict[str, Any]) -> Any:
        return await self.execute_function_with_retry(params)


async def hello_plugin(ctx):  # pragma: no cover - example code
    if "hello" in ctx.message.lower():
        return "Hello there!"
    return None


class WeatherTool(ToolPlugin):
    """Return a canned weather string."""

    stages = [PipelineStage.DO]
    name = "weather"

    async def execute_function(self, params: Dict[str, Any]) -> str:
        city = params.get("city", "San Francisco")
        return f"Weather in {city} is sunny"

    async def execute(self, params: Dict[str, Any]) -> str:
        return await self.execute_function_with_retry(params)


def create_llm() -> UnifiedLLMResource:
    """Return a configured LLM resource."""

    base_url = os.getenv("OLLAMA_BASE_URL")
    model = os.getenv("OLLAMA_MODEL")
    if base_url and model:
        cfg = {"provider": "ollama", "base_url": base_url, "model": model}
    else:
        cfg = {"provider": "echo"}
    return UnifiedLLMResource(cfg)


async def main() -> None:  # pragma: no cover - example code
    load_env()
    builder = AgentBuilder()
    await builder.tool_registry.add("weather", WeatherTool())
    await builder.tool_registry.add("calculator", CalculatorTool())
    await builder.resource_registry.add("llm", create_llm())
    builder.plugin(hello_plugin, stages=[PipelineStage.DO], name="hello_plugin")

    runtime = builder.build_runtime()
    workflow = Workflow({PipelineStage.DO: ["hello_plugin"]})
    pipeline = Pipeline(approach=workflow)
    response = await pipeline.run_message("hello", runtime.capabilities)
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
