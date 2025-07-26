from __future__ import annotations

from entity.plugins import Plugin
from entity.workflow.executor import WorkflowExecutor

from tests.plugin_test_base import PluginValidationTests, PluginDependencyTests


class ExamplePlugin(Plugin):
    stage = WorkflowExecutor.THINK
    dependencies = ["memory"]

    class ConfigModel(Plugin.ConfigModel):
        value: int

    async def _execute_impl(self, context):  # pragma: no cover - not executed
        return "ok"


class TestExamplePlugin(PluginValidationTests, PluginDependencyTests):
    Plugin = ExamplePlugin
    stage = WorkflowExecutor.THINK
    config = {"value": 1}
    resources = {}
