from __future__ import annotations

import pytest

from entity.workflow.workflow import Workflow, WorkflowConfigError
from entity.workflow.executor import WorkflowExecutor


class DummyPlugin:
    stage = WorkflowExecutor.THINK

    async def _execute_impl(self, context):
        return "ok"


class MultiStagePlugin:
    supported_stages = [WorkflowExecutor.PARSE, WorkflowExecutor.REVIEW]

    async def _execute_impl(self, context):
        return "ok"


def test_from_dict_loads_plugins():
    wf = Workflow.from_dict({"think": [DummyPlugin]})
    assert wf.plugins_for("think") == [DummyPlugin]


def test_validation_rejects_invalid_stage():
    with pytest.raises(WorkflowConfigError):
        Workflow.from_dict({"do": [DummyPlugin]})


def test_validation_uses_supported_stages():
    with pytest.raises(WorkflowConfigError):
        Workflow.from_dict({"think": [MultiStagePlugin]})
