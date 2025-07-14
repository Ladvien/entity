import logging
<<<<<<< HEAD

from entity.pipeline.utils import StageResolver
from entity.core.stages import PipelineStage
from entity.core.plugins import Plugin, PromptPlugin

=======
from entity.pipeline import utils as pipeline_utils
from entity.core.stages import PipelineStage
from entity.core.plugins import Plugin, PromptPlugin

StageResolver = pipeline_utils.StageResolver

>>>>>>> pr-1582

class AttrPrompt(Plugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        # Add any custom implementation if needed
        pass


class InferredPrompt(Plugin):
    async def _execute_impl(self, context):
        # Add any custom implementation if needed
        pass


class DerivedPrompt(PromptPlugin):
    async def _execute_impl(self, context):
        # Add any custom implementation if needed
        pass


def test_builder_config_overrides():
    """Test if config overrides the builder's stage configuration."""
    plugin = AttrPrompt({})
    stages, _ = StageResolver._resolve_plugin_stages(
        plugin.__class__, {"stage": PipelineStage.REVIEW}, plugin
    )
    assert stages == [PipelineStage.REVIEW]


def test_builder_class_attribute_overrides():
    """Test if class attributes override builder configuration."""
    plugin = AttrPrompt({})
    stages, _ = StageResolver._resolve_plugin_stages(
        plugin.__class__, plugin.config, plugin
    )
    assert stages == [PipelineStage.DO]


def test_builder_fallback_stage():
    """Test if the builder falls back to the default stage."""
    plugin = InferredPrompt({})
    stages, _ = StageResolver._resolve_plugin_stages(
        plugin.__class__, plugin.config, plugin
    )
    assert stages == [PipelineStage.THINK]


def test_initializer_config_overrides():
    """Test if config overrides the initializer's stage."""
    plugin = AttrPrompt({})
    plugin._explicit_stages = True
    stages, explicit = StageResolver._resolve_plugin_stages(
        AttrPrompt, {"stage": PipelineStage.REVIEW}, plugin
    )
    assert stages == [PipelineStage.REVIEW]
    assert explicit is True


def test_initializer_class_attribute_overrides():
    """Test if class attributes override initializer configuration."""
    plugin = AttrPrompt({})
    plugin._explicit_stages = True
    stages, explicit = StageResolver._resolve_plugin_stages(AttrPrompt, {}, plugin)
    assert stages == [PipelineStage.DO]
    assert explicit is True


def test_initializer_fallback_stage():
    """Test if the initializer falls back to the default stage."""
    plugin = InferredPrompt({})
    stages, explicit = StageResolver._resolve_plugin_stages(InferredPrompt, {}, plugin)
    assert stages == [PipelineStage.THINK]
    assert explicit is False


def test_initializer_inherited_stage_not_explicit():
    """Test if inherited stages are not explicit."""
    plugin = DerivedPrompt({})
    stages, explicit = StageResolver._resolve_plugin_stages(DerivedPrompt, {}, plugin)
    assert stages == [PipelineStage.THINK]
    assert explicit is False


def test_warning_for_stage_override(caplog):
    """Test if a warning is logged when a stage override occurs."""
    plugin = AttrPrompt({})
    with caplog.at_level(logging.WARNING):
        StageResolver._resolve_plugin_stages(
            AttrPrompt, {"stage": PipelineStage.REVIEW}, plugin
        )
    assert any("configuration stages" in r.message for r in caplog.records)
