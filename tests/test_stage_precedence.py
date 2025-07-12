from entity.core.builder import _AgentBuilder
from entity.core.plugins import Plugin
from pipeline.initializer import SystemInitializer
from entity.core.stages import PipelineStage


class AttrPrompt(Plugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        pass


class InferredPrompt(Plugin):
    async def _execute_impl(self, context):
        pass


def test_builder_config_overrides():
    builder = _AgentBuilder()
    plugin = AttrPrompt({})

    stages = builder._resolve_plugin_stages(plugin, {"stage": PipelineStage.REVIEW})

    assert stages == [PipelineStage.REVIEW]


def test_builder_class_attribute_overrides():
    builder = _AgentBuilder()
    plugin = AttrPrompt({})
    stages = builder._resolve_plugin_stages(plugin, None)

    assert stages == [PipelineStage.DO]


def test_builder_type_default():
    builder = _AgentBuilder()
    plugin = InferredPrompt({})
    stages = builder._resolve_plugin_stages(plugin, None)

    assert stages == [PipelineStage.THINK]


def test_initializer_config_overrides():
    init = SystemInitializer({})
    plugin = AttrPrompt({})
    plugin._explicit_stages = True

    stages, explicit = init._resolve_plugin_stages(
        AttrPrompt, plugin, {"stage": PipelineStage.REVIEW}
    )

    assert stages == [PipelineStage.REVIEW]
    assert explicit is True


def test_initializer_class_attribute_overrides():
    init = SystemInitializer({})
    plugin = AttrPrompt({})
    plugin._explicit_stages = True

    stages, explicit = init._resolve_plugin_stages(AttrPrompt, plugin, {})

    assert stages == [PipelineStage.DO]
    assert explicit is True


def test_initializer_type_default():
    init = SystemInitializer({})
    plugin = InferredPrompt({})

    stages, explicit = init._resolve_plugin_stages(InferredPrompt, plugin, {})

    assert stages == [PipelineStage.THINK]
    assert explicit is False
