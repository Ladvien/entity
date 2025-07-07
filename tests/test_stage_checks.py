import pytest

from pipeline import PipelineStage, PluginRegistry, PromptPlugin


class GoodPlugin(PromptPlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        pass


def test_plugin_without_stages_allowed():
    class NoStages(PromptPlugin):
        async def _execute_impl(self, context):
            pass

    NoStages()


def test_plugin_invalid_stage():
    with pytest.raises(ValueError):

        class BadStage(PromptPlugin):
            stages = ["bogus"]

            async def _execute_impl(self, context):
                pass


def test_registry_rejects_invalid_stage():
    reg = PluginRegistry()
    plugin = GoodPlugin({})
    with pytest.raises(ValueError):
        reg.register_plugin_for_stage(plugin, "bogus")
