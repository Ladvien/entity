from entity.core.builder import _AgentBuilder
from entity.core.plugin_utils import PluginAutoClassifier
from entity.core.plugins import PromptPlugin
from entity.core.stages import PipelineStage


class AttrPrompt(PromptPlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        pass


class InferredPrompt(PromptPlugin):
    async def _execute_impl(self, context):
        pass


def test_config_overrides_class_and_defaults():
    builder = _AgentBuilder()
    plugin = AttrPrompt({})
    stages = builder._resolve_plugin_stages(plugin, {"stage": PipelineStage.REVIEW})
    assert stages == [PipelineStage.REVIEW]


def test_class_attribute_overrides_type_defaults():
    builder = _AgentBuilder()
    plugin = AttrPrompt({})
    stages = builder._resolve_plugin_stages(plugin, None)
    assert stages == [PipelineStage.DO]


def test_type_default_overrides_auto_classification():
    builder = _AgentBuilder()
    plugin = InferredPrompt({})
    plugin.stages = [PipelineStage.OUTPUT]
    plugin._explicit_stages = False
    stages = builder._resolve_plugin_stages(plugin, None)
    assert stages == [PipelineStage.THINK]


def test_auto_classification_used_when_no_other_source():
    builder = _AgentBuilder()

    async def fn(ctx):
        return None

    plugin = PluginAutoClassifier.classify(fn)
    stages = builder._resolve_plugin_stages(plugin, None)
    assert stages == [PipelineStage.THINK]
