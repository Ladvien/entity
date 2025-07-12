from entity.core.builder import _AgentBuilder
from entity.core.plugins import Plugin
from entity.core.stages import PipelineStage
from pipeline.initializer import SystemInitializer


class AttrPrompt(Plugin):
    """Prompt with a stage defined as a class attribute."""

    stages = [PipelineStage.DO]

    async def _execute_impl(self, context) -> None:  # pragma: no cover - stub
        pass


class NoStagePrompt(Plugin):
    """Prompt without any stage information."""

    async def _execute_impl(self, context) -> None:  # pragma: no cover - stub
        pass


def test_builder_config_overrides() -> None:
    builder = _AgentBuilder()
    plugin = AttrPrompt({})

    stages = builder._resolve_plugin_stages(plugin, {"stage": PipelineStage.REVIEW})

    assert stages == [PipelineStage.REVIEW]


def test_builder_class_attribute_when_no_config() -> None:
    builder = _AgentBuilder()
    plugin = AttrPrompt({})

    stages = builder._resolve_plugin_stages(plugin, None)

    assert stages == [PipelineStage.DO]


def test_builder_defaults_to_think() -> None:
    builder = _AgentBuilder()
    plugin = NoStagePrompt({})

    stages = builder._resolve_plugin_stages(plugin, None)

    assert stages == [PipelineStage.THINK]


def test_initializer_config_overrides() -> None:
    init = SystemInitializer({})
    plugin = AttrPrompt({})

    stages, _ = init._resolve_plugin_stages(
        AttrPrompt, plugin, {"stage": PipelineStage.REVIEW}
    )

    assert stages == [PipelineStage.REVIEW]


def test_initializer_class_attribute_when_no_config() -> None:
    init = SystemInitializer({})
    plugin = AttrPrompt({})

    stages, _ = init._resolve_plugin_stages(AttrPrompt, plugin, {})

    assert stages == [PipelineStage.DO]


def test_initializer_defaults_to_think() -> None:
    init = SystemInitializer({})
    plugin = NoStagePrompt({})

    stages, _ = init._resolve_plugin_stages(NoStagePrompt, plugin, {})

    assert stages == [PipelineStage.THINK]
