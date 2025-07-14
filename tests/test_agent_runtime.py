import pytest

from entity.core.agent import Agent
from entity.core.plugins import Plugin
from entity.pipeline.stages import PipelineStage
from entity.pipeline.workflow import Pipeline, Workflow


class ThoughtPlugin(Plugin):
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context):
        last = context.conversation()[-1].content
        await context.think("msg", last)


class EchoPlugin(Plugin):
    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context):
        msg = await context.reflect("msg")
        context.say(f"{msg}!")


@pytest.mark.asyncio
async def test_builder_runtime_executes_workflow():
    builder = Agent().builder
    await builder.add_plugin(ThoughtPlugin({}))
    await builder.add_plugin(EchoPlugin({}))
    wf = Workflow(
        {
            PipelineStage.THINK: ["ThoughtPlugin"],
            PipelineStage.OUTPUT: ["EchoPlugin"],
        }
    )
    pipeline = Pipeline(builder=builder, workflow=wf)
    runtime = await pipeline.build_runtime()
    result = await runtime.handle("hello")
    assert result == "hello!"


@pytest.mark.asyncio
async def test_agent_handle_runs_workflow():
    agent = Agent()
    await agent.add_plugin(ThoughtPlugin({}))
    await agent.add_plugin(EchoPlugin({}))
    wf = Workflow(
        {PipelineStage.THINK: ["ThoughtPlugin"], PipelineStage.OUTPUT: ["EchoPlugin"]}
    )
    agent.pipeline = Pipeline(builder=agent.builder, workflow=wf)
    result = await agent.handle("bye")
    assert result == "bye!"


@pytest.mark.asyncio
async def test_builder_registers_default_resources() -> None:
    builder = Agent().builder
    runtime = await builder.build_runtime()
    assert runtime is not None
    assert builder.resource_registry.get("memory") is not None
    assert builder.resource_registry.get("llm") is not None
    assert builder.resource_registry.get("storage") is not None
    mem = builder.resource_registry.get("memory")
    assert getattr(mem, "database", None) is not None
