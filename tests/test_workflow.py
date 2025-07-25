from __future__ import annotations

import pytest

from entity.plugins.base import Plugin
from entity.resources.memory import Memory
from entity.resources.database import DatabaseResource
from entity.resources.vector_store import VectorStoreResource
from entity.infrastructure.duckdb_infra import DuckDBInfrastructure

from entity.workflow.workflow import Workflow, WorkflowConfigError
from entity.workflow.executor import WorkflowExecutor


class DummyPlugin(Plugin):
    supported_stages = [WorkflowExecutor.THINK]

    async def _execute_impl(self, context):
        return "ok"


class MultiStagePlugin(Plugin):
    supported_stages = [WorkflowExecutor.PARSE, WorkflowExecutor.REVIEW]

    async def _execute_impl(self, context):
        return "ok"


def test_from_dict_loads_plugins():
    wf = Workflow.from_dict({"think": [DummyPlugin]}, resources={})
    assert wf.plugins_for("think")[0].__class__ == DummyPlugin


def test_validation_rejects_invalid_stage():
    with pytest.raises(WorkflowConfigError):
        Workflow.from_dict({"foobar": [DummyPlugin]}, resources={})


def test_validation_uses_supported_stages():
    wf = Workflow.from_dict({"think": [MultiStagePlugin]}, resources={})
    assert wf.plugins_for("think")[0].__class__ == MultiStagePlugin


class FailingPlugin(Plugin):
    supported_stages = [WorkflowExecutor.THINK]

    async def _execute_impl(self, context):
        raise RuntimeError("boom")


called = []


class ErrorPlugin(Plugin):
    supported_stages = [WorkflowExecutor.ERROR]

    async def _execute_impl(self, context):
        called.append(context.message)


class RecoveryPlugin(Plugin):
    supported_stages = [WorkflowExecutor.ERROR]

    async def _execute_impl(self, context):
        context.say("recovered")


@pytest.mark.asyncio
async def test_error_hook_runs_on_failure():
    wf = {
        WorkflowExecutor.THINK: [FailingPlugin],
        WorkflowExecutor.ERROR: [ErrorPlugin],
    }
    infra = DuckDBInfrastructure(":memory:")
    memory = Memory(DatabaseResource(infra), VectorStoreResource(infra))
    resources = {"memory": memory}
    wf_obj = Workflow.from_dict(wf, resources)
    executor = WorkflowExecutor(resources, wf_obj)
    with pytest.raises(RuntimeError):
        await executor.execute("hello")
    assert called == ["boom"]


@pytest.mark.asyncio
async def test_error_hook_recovers():
    wf = {
        WorkflowExecutor.THINK: [FailingPlugin],
        WorkflowExecutor.ERROR: [RecoveryPlugin],
    }
    infra = DuckDBInfrastructure(":memory:")
    memory = Memory(DatabaseResource(infra), VectorStoreResource(infra))
    resources = {"memory": memory}
    wf_obj = Workflow.from_dict(wf, resources)
    executor = WorkflowExecutor(resources, wf_obj)
    result = await executor.execute("oops")
    assert result == "recovered"


class LoopingOutput(Plugin):
    supported_stages = [WorkflowExecutor.OUTPUT]

    async def _execute_impl(self, context):
        if getattr(context, "loop_count", 0) >= 2:
            context.say("done")
            return "done"
        return f"loop{getattr(context, 'loop_count', 0)}"


@pytest.mark.asyncio
async def test_executor_repeats_until_response():
    wf = {WorkflowExecutor.OUTPUT: [LoopingOutput]}
    infra = DuckDBInfrastructure(":memory:")
    memory = Memory(DatabaseResource(infra), VectorStoreResource(infra))
    resources = {"memory": memory}
    wf_obj = Workflow.from_dict(wf, resources)
    executor = WorkflowExecutor(resources, wf_obj)

    result = await executor.execute("hi")
    assert result == "done"
