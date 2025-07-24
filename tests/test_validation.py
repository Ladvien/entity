import pytest

from entity.config.validation import validate_config, validate_workflow
from entity.workflow.workflow import Workflow, WorkflowConfigError
from entity.plugins import Plugin
from entity.workflow.executor import WorkflowExecutor


class DummyPlugin(Plugin):
    stage = WorkflowExecutor.THINK

    class ConfigModel(Plugin.ConfigModel):
        value: int = 0

    async def _execute_impl(self, context):
        return "ok"


class MultiStagePlugin(Plugin):
    supported_stages = [WorkflowExecutor.PARSE]

    async def _execute_impl(self, context):
        return "ok"


def test_validate_config_success(tmp_path):
    cfg = tmp_path / "conf.yml"
    cfg.write_text("resources: {}\nworkflow: {}")
    data = validate_config(cfg)
    assert data == {"resources": {}, "workflow": {}}


def test_validate_config_missing(tmp_path):
    cfg = tmp_path / "bad.yml"
    cfg.write_text("workflow: {}")
    with pytest.raises(ValueError):
        validate_config(cfg)


def test_validate_workflow_pass():
    wf = Workflow(steps={"think": [DummyPlugin]})
    validate_workflow(wf)


def test_validate_workflow_fail_stage():
    wf = Workflow(steps={"unknown": [DummyPlugin]})
    with pytest.raises(WorkflowConfigError):
        validate_workflow(wf)


def test_validate_workflow_fail_plugin():
    wf = Workflow(steps={"think": [MultiStagePlugin]})
    with pytest.raises(WorkflowConfigError):
        validate_workflow(wf)


def test_plugin_config_validation():
    class TestPlugin(Plugin):
        stage = WorkflowExecutor.THINK

        class ConfigModel(Plugin.ConfigModel):
            value: int

        async def _execute_impl(self, context):
            return "ok"

    with pytest.raises(ValueError):
        TestPlugin({}, config={"value": "bad"})
