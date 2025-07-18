import logging
import pytest

from entity.core.context import PluginContext
from entity.core.plugins import (
    InputAdapterPlugin,
    OutputAdapterPlugin,
    Plugin,
    PromptPlugin,
)
from entity.core.registries import ToolRegistry
from entity.core.state import PipelineState
from entity.pipeline.errors import PluginContextError
from entity.core.stages import PipelineStage
from entity.core.stage_utils import StageResolver


class AttrPlugin(Plugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context: PluginContext) -> None:
        pass


class SayDuringParse(PromptPlugin):
    stages = [PipelineStage.PARSE]

    async def _execute_impl(self, context: PluginContext) -> None:
        context.say("oops")


class DummyRegs:
    def __init__(self) -> None:
        self.resources = {}
        self.tools = ToolRegistry()


def make_context(stage: PipelineStage) -> PluginContext:
    state = PipelineState(conversation=[])
    ctx = PluginContext(state, DummyRegs())
    ctx.set_current_stage(stage)
    ctx.set_current_plugin("test")
    return ctx


def test_config_overrides_class_stage(caplog: pytest.LogCaptureFixture) -> None:
    logger = logging.getLogger("stage-test")
    with caplog.at_level(logging.WARNING):
        stages, _ = StageResolver._resolve_plugin_stages(
            AttrPlugin,
            {"stage": PipelineStage.REVIEW},
            logger=logger,
        )
    assert stages == [PipelineStage.REVIEW]
    assert "configuration stages" in caplog.text


def test_fallback_stage_not_explicit() -> None:
    class NoStagePlugin(Plugin):
        async def _execute_impl(self, context: PluginContext) -> None:
            pass

    stages, explicit = StageResolver._resolve_plugin_stages(NoStagePlugin, {})
    assert stages == [PipelineStage.THINK]
    assert explicit is False


def test_class_stage_used_without_config() -> None:
    stages, _ = StageResolver._resolve_plugin_stages(AttrPlugin, {})
    assert stages == [PipelineStage.DO]


@pytest.mark.asyncio
async def test_say_only_allowed_for_output() -> None:
    ctx = make_context(PipelineStage.PARSE)
    plugin = SayDuringParse({})
    with pytest.raises(PluginContextError):
        await plugin.execute(ctx)


class DummyInput(InputAdapterPlugin):
    async def _execute_impl(self, context: PluginContext) -> None:
        pass


class DummyOutput(OutputAdapterPlugin):
    async def _execute_impl(self, context: PluginContext) -> None:
        pass


def test_stage_resolution_for_input_adapter(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        stages, _ = StageResolver._resolve_plugin_stages(
            DummyInput,
            {"stage": PipelineStage.OUTPUT},
            logger=logging.getLogger("stage-test"),
        )
    assert stages == [PipelineStage.INPUT]
    assert "INPUT stage" in caplog.text


def test_stage_resolution_for_output_adapter(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        stages, _ = StageResolver._resolve_plugin_stages(
            DummyOutput,
            {"stage": PipelineStage.INPUT},
            logger=logging.getLogger("stage-test"),
        )
    assert stages == [PipelineStage.OUTPUT]
    assert "OUTPUT stage" in caplog.text
