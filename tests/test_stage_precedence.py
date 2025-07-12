from entity.core.plugins import Plugin
from entity.pipeline.utils import StageResolver
from entity.core.stages import PipelineStage


class AttrPrompt(Plugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        pass


class InferredPrompt(Plugin):
    async def _execute_impl(self, context):
        pass


def test_builder_config_overrides():
    plugin = AttrPrompt({})

    stages, _ = StageResolver._resolve_plugin_stages(
        plugin.__class__, {"stage": PipelineStage.REVIEW}, plugin
    )

    assert stages == [PipelineStage.REVIEW]


def test_builder_class_attribute_overrides():
    plugin = AttrPrompt({})
    stages, _ = StageResolver._resolve_plugin_stages(
        plugin.__class__, plugin.config, plugin
    )

    assert stages == [PipelineStage.DO]


def test_builder_fallback_stage():
    plugin = InferredPrompt({})
    stages, _ = StageResolver._resolve_plugin_stages(
        plugin.__class__, plugin.config, plugin
    )

    assert stages == [PipelineStage.THINK]


def test_initializer_config_overrides():
    plugin = AttrPrompt({})
    plugin._explicit_stages = True

    stages, explicit = StageResolver._resolve_plugin_stages(
        AttrPrompt, {"stage": PipelineStage.REVIEW}, plugin
    )

    assert stages == [PipelineStage.REVIEW]
    assert explicit is True


def test_initializer_class_attribute_overrides():
    plugin = AttrPrompt({})
    plugin._explicit_stages = True

    stages, explicit = StageResolver._resolve_plugin_stages(AttrPrompt, {}, plugin)

    assert stages == [PipelineStage.DO]
    assert explicit is True


def test_initializer_fallback_stage():
    plugin = InferredPrompt({})

    stages, explicit = StageResolver._resolve_plugin_stages(InferredPrompt, {}, plugin)

    assert stages == [PipelineStage.THINK]
    assert explicit is False
