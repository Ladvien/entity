import pytest

from entity.core.agent import Agent
from entity.core.plugins import Plugin
from entity.infrastructure import DuckDBInfrastructure
from entity.pipeline.stages import PipelineStage
from entity.pipeline.workflow import Pipeline, Workflow
from entity.resources.interfaces.duckdb_resource import DuckDBResource
from entity.resources.interfaces.duckdb_vector_store import DuckDBVectorStore


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
    agent = Agent()
    builder = agent.builder
    await builder.add_plugin(ThoughtPlugin({}))
    await builder.add_plugin(EchoPlugin({}))
    wf = Workflow(
        {
            PipelineStage.THINK: ["ThoughtPlugin"],
            PipelineStage.OUTPUT: ["EchoPlugin"],
        }
    )
    pipeline = Pipeline(builder=builder, workflow=wf)
    agent.register_resource("database_backend", DuckDBInfrastructure, {}, layer=1)
    agent.register_resource("database", DuckDBResource, {}, layer=2)
    agent.register_resource("vector_store", DuckDBVectorStore, {}, layer=2)
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
    agent.register_resource("database_backend", DuckDBInfrastructure, {}, layer=1)
    agent.register_resource("database", DuckDBResource, {}, layer=2)
    agent.register_resource("vector_store", DuckDBVectorStore, {}, layer=2)
    result = await agent.handle("bye")
    assert result == "bye!"


@pytest.mark.asyncio
async def test_builder_registers_default_resources() -> None:
    agent = Agent()
    agent.register_resource("database_backend", DuckDBInfrastructure, {}, layer=1)
    agent.register_resource("database", DuckDBResource, {}, layer=2)
    agent.register_resource("vector_store", DuckDBVectorStore, {}, layer=2)
    runtime = await agent.build_runtime()
    assert runtime is not None
    assert builder.resource_registry.get("memory") is not None
    assert builder.resource_registry.get("llm") is not None
    assert builder.resource_registry.get("llm_provider") is not None
    assert builder.resource_registry.get("echo_llm_backend") is not None
    assert builder.resource_registry.get("storage") is not None
    mem = builder.resource_registry.get("memory")
    assert getattr(mem, "database", None) is not None
