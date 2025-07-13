from entity.core.plugins import Plugin, PromptPlugin
import importlib
import logging
import entity.pipeline.utils as pipeline_utils
from entity.core.stages import PipelineStage

# Reload pipeline_utils to ensure the original StageResolver is used
StageResolver = importlib.reload(pipeline_utils).StageResolver

# Reload pipeline utilities to restore the original StageResolver in case other
# tests have replaced it.  This ensures explicit stage detection works as
# expected in these tests.
pipeline_utils = importlib.reload(pipeline_utils)
StageResolver = pipeline_utils.StageResolver

# Reload pipeline utilities to restore the original StageResolver in case other
# tests have replaced it.  This ensures explicit stage detection works as
# expected in these tests.
pipeline_utils = importlib.reload(pipeline_utils)
StageResolver = pipeline_utils.StageResolver


class AttrPrompt(Plugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        pass


class InferredPrompt(Plugin):
    async def _execute_impl(self, context):
        pass


class DerivedPrompt(PromptPlugin):
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
    # The initializer treats the default THINK stage as explicit
    assert explicit is True


def test_initializer_inherited_stage_not_explicit():
    plugin = DerivedPrompt({})

    stages, explicit = StageResolver._resolve_plugin_stages(DerivedPrompt, {}, plugin)

    assert stages == [PipelineStage.THINK]
    assert explicit is False


def test_warning_for_stage_override(caplog):
    plugin = AttrPrompt({})
    with caplog.at_level(logging.WARNING):
        StageResolver._resolve_plugin_stages(
            AttrPrompt, {"stage": PipelineStage.REVIEW}, plugin
        )
    assert any("differ from declared" in r.message for r in caplog.records)
