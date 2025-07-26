from __future__ import annotations

from entity.plugins import Plugin


from tests.plugin_test_base import PluginValidationTests, PluginDependencyTests


class ExamplePlugin(Plugin):
    supported_stages = ["think"]
    dependencies = ["memory"]

    class ConfigModel(Plugin.ConfigModel):
        value: int

    async def _execute_impl(self, context):
        return "ok"


class TestExamplePlugin(PluginValidationTests, PluginDependencyTests):
    Plugin = ExamplePlugin
    stage = "think"
    config = {"value": 1}
    resources = {"memory": object()}
