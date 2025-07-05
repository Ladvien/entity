import asyncio

import pytest

from pipeline import PipelineStage, PluginRegistry, PromptPlugin


class GoodPlugin(PromptPlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        pass


def test_plugin_requires_stages():
    with pytest.raises(ValueError):

        class NoStages(PromptPlugin):
            pass


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
        asyncio.run(reg.register_plugin_for_stage(plugin, "bogus"))
