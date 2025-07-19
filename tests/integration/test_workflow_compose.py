import pytest

from entity.core.agent import Agent
from entity.core.plugins import Plugin
from entity.infrastructure import DuckDBInfrastructure
from entity.pipeline.stages import PipelineStage
from entity.resources.database import DuckDBResource
from entity.resources.duckdb_vector_store import DuckDBVectorStore
from entity.infrastructure.duckdb_vector import DuckDBVectorInfrastructure
from entity.workflows.base import Workflow
from entity.workflows.compose import compose_workflows


class MarkerPlugin(Plugin):
    stages = [PipelineStage.THINK]
    executed = False

    async def _execute_impl(self, context):
        MarkerPlugin.executed = True


class EchoPlugin(Plugin):
    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context):
        context.say("ok")


class WF1(Workflow):
    stage_map = {PipelineStage.THINK: ["MarkerPlugin"]}


class WF2(Workflow):
    stage_map = {PipelineStage.OUTPUT: ["EchoPlugin"]}


@pytest.mark.asyncio
async def test_compose_workflows_execute():
    MarkerPlugin.executed = False
    agent = Agent()
    builder = agent.builder
    await builder.add_plugin(MarkerPlugin({}))
    await builder.add_plugin(EchoPlugin({}))

    wf = compose_workflows(WF1(), WF2())
    agent.register_resource("database_backend", DuckDBInfrastructure, {}, layer=1)
    agent.register_resource("database", DuckDBResource, {}, layer=2)
    agent.register_resource(
        "vector_store_backend", DuckDBVectorInfrastructure, {}, layer=1
    )
    agent.register_resource("vector_store", DuckDBVectorStore, {}, layer=2)
    runtime = await builder.build_runtime(wf)
    result = await runtime.handle("hi")

    assert result == "ok"
    assert MarkerPlugin.executed


@pytest.mark.asyncio
async def test_compose_validates_plugins():
    agent = Agent()
    builder = agent.builder
    await builder.add_plugin(EchoPlugin({}))

    wf = compose_workflows(WF1(), WF2())
    agent.register_resource("database_backend", DuckDBInfrastructure, {}, layer=1)
    agent.register_resource("database", DuckDBResource, {}, layer=2)
    agent.register_resource(
        "vector_store_backend", DuckDBVectorInfrastructure, {}, layer=1
    )
    agent.register_resource("vector_store", DuckDBVectorStore, {}, layer=2)
    with pytest.raises(KeyError):
        await builder.build_runtime(wf)
