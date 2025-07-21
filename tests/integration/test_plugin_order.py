from __future__ import annotations

import pytest

from entity.pipeline.initializer import SystemInitializer
from entity.core.context import PluginContext
from entity.core.plugins import PromptPlugin
from entity.core.registries import SystemRegistries
from entity.pipeline.stages import PipelineStage
from entity.worker.pipeline_worker import PipelineWorker


class Step1(PromptPlugin):
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context: PluginContext) -> None:
        steps = await context.reflect("steps", [])
        steps.append("Step1")
        await context.think("steps", steps)


class Step2(PromptPlugin):
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context: PluginContext) -> None:
        steps = await context.reflect("steps", [])
        steps.append("Step2")
        await context.think("steps", steps)


class Step3(PromptPlugin):
    stages = [PipelineStage.THINK]
    result: list[str] | None = None

    async def _execute_impl(self, context: PluginContext) -> None:
        steps = await context.reflect("steps", [])
        steps.append("Step3")
        await context.think("steps", steps)
        Step3.result = steps


class Finish(PromptPlugin):
    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context: PluginContext) -> None:
        await context.say("done")


@pytest.mark.skip(reason="Prompt plugins can no longer run in the OUTPUT stage.")
@pytest.mark.asyncio
async def test_prompt_plugin_order(tmp_path) -> None:
    config = f"""
plugins:
  prompts:
    step_1:
      type: {__name__}:Step1
      stage: think
    step_2:
      type: {__name__}:Step2
      stage: think
    step_3:
      type: {__name__}:Step3
      stage: think
    finish:
      type: {__name__}:Finish
      stage: output
workflow:
  stages:
    THINK:
      - step_1
      - step_2
      - step_3
    OUTPUT:
      - finish
"""
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(config)

    initializer = SystemInitializer.from_yaml(str(cfg_path))
    plugins, resources, tools, workflow = await initializer.initialize()
    registries = SystemRegistries(resources=resources, tools=tools, plugins=plugins)

    worker = PipelineWorker(registries)
    result = await worker.execute_pipeline("order", "hi", user_id="u1")

    assert result == "done"
    assert Step3.result == ["Step1", "Step2", "Step3"]
