import asyncio

import pytest
from pipeline import (
    ClassRegistry,
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    BasePlugin,
)


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
        asyncio.run(reg.register_plugin_for_stage(plugin, "bogus"))


def test_class_registry_validates_missing_stage():
    class PlainPlugin(BasePlugin):
        async def _execute_impl(self, context):
            pass

    reg = ClassRegistry()
    with pytest.raises(SystemError, match="No stage"):
        reg.register_class(PlainPlugin, {}, "plain")


def test_class_registry_validates_invalid_stage():
    class BadStage(BasePlugin):
        stages = ["bogus"]

        async def _execute_impl(self, context):
            pass

    reg = ClassRegistry()
    with pytest.raises(ValueError):
        reg.register_class(BadStage, {}, "bad")
