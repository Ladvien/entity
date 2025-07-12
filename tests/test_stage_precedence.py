import logging

from entity.core.builder import _AgentBuilder
from entity.core.plugin_utils import PluginAutoClassifier
from entity.core.plugins import PromptPlugin
from pipeline.initializer import SystemInitializer
from entity.core.stages import PipelineStage


class AttrPrompt(PromptPlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        pass


class InferredPrompt(PromptPlugin):
    async def _execute_impl(self, context):
        pass


def test_builder_config_overrides(caplog):
    builder = _AgentBuilder()
    plugin = AttrPrompt({})
    caplog.set_level(logging.WARNING, logger="entity.core.builder")
    logging.getLogger("entity.core.builder").addHandler(caplog.handler)

    stages = builder._resolve_plugin_stages(plugin, {"stage": PipelineStage.REVIEW})

    assert stages == [PipelineStage.REVIEW]
    assert any("override class stages" in r.getMessage() for r in caplog.records)
    assert any("override type defaults" in r.getMessage() for r in caplog.records)


def test_builder_class_attribute_overrides(caplog):
    builder = _AgentBuilder()
    plugin = AttrPrompt({})
    caplog.set_level(logging.WARNING, logger="entity.core.builder")

    stages = builder._resolve_plugin_stages(plugin, None)

    assert stages == [PipelineStage.DO]
    assert any("override type defaults" in r.getMessage() for r in caplog.records)


def test_builder_type_default(caplog):
    builder = _AgentBuilder()
    plugin = InferredPrompt({})
    caplog.set_level(logging.WARNING, logger="entity.core.builder")
    logging.getLogger("entity.core.builder").addHandler(caplog.handler)

    stages = builder._resolve_plugin_stages(plugin, None)

    assert stages == [PipelineStage.THINK]
    assert not caplog.records


def test_builder_auto_classification(caplog):
    builder = _AgentBuilder()

    async def fn(ctx):
        return None

    plugin = PluginAutoClassifier.classify(fn, {"plugin_class": PromptPlugin})
    caplog.set_level(logging.WARNING, logger="entity.core.builder")
    logging.getLogger("entity.core.builder").addHandler(caplog.handler)

    stages = builder._resolve_plugin_stages(plugin, None)

    assert stages == [PipelineStage.THINK]
    assert not caplog.records


def test_initializer_config_overrides(caplog):
    init = SystemInitializer({})
    plugin = AttrPrompt({})
    plugin._explicit_stages = True
    caplog.set_level(logging.WARNING, logger="pipeline.initializer")
    logging.getLogger("pipeline.initializer").addHandler(caplog.handler)

    stages, explicit = init._resolve_plugin_stages(
        AttrPrompt, plugin, {"stage": PipelineStage.REVIEW}
    )

    assert stages == [PipelineStage.REVIEW]
    assert explicit is True
    assert any("override class stages" in r.getMessage() for r in caplog.records)
    assert any("override type defaults" in r.getMessage() for r in caplog.records)


def test_initializer_class_attribute_overrides(caplog):
    init = SystemInitializer({})
    plugin = AttrPrompt({})
    plugin._explicit_stages = True
    caplog.set_level(logging.WARNING, logger="pipeline.initializer")

    stages, explicit = init._resolve_plugin_stages(AttrPrompt, plugin, {})

    assert stages == [PipelineStage.DO]
    assert explicit is True
    assert any("override type defaults" in r.getMessage() for r in caplog.records)


def test_initializer_type_default(caplog):
    init = SystemInitializer({})
    plugin = InferredPrompt({})
    caplog.set_level(logging.WARNING, logger="pipeline.initializer")
    logging.getLogger("pipeline.initializer").addHandler(caplog.handler)

    stages, explicit = init._resolve_plugin_stages(InferredPrompt, plugin, {})

    assert stages == [PipelineStage.THINK]
    assert explicit is False
    assert not caplog.records


def test_initializer_auto_classification(caplog):
    init = SystemInitializer({})

    async def fn(ctx):
        return None

    plugin = PluginAutoClassifier.classify(fn, {"plugin_class": PromptPlugin})
    caplog.set_level(logging.WARNING, logger="pipeline.initializer")
    logging.getLogger("pipeline.initializer").addHandler(caplog.handler)

    stages, explicit = init._resolve_plugin_stages(plugin.__class__, plugin, {})

    assert stages == [PipelineStage.THINK]
    assert explicit is False
    assert not caplog.records
