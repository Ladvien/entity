import pytest
from entity.core.context import PluginContext
from entity.core.plugins import Plugin, PromptPlugin
from entity.core.registries import ToolRegistry
from entity.core.stages import PipelineStage
from entity.core.state import PipelineState
from entity.pipeline.errors import PluginContextError
from entity.pipeline.utils import resolve_stages


class AttrPlugin(Plugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        pass


class NoStagePlugin(Plugin):
    async def _execute_impl(self, context):
        pass


def test_config_overrides_class_stage() -> None:
    stages = resolve_stages(AttrPlugin, {"stage": PipelineStage.PARSE})
    assert stages == [PipelineStage.PARSE]


def test_class_stage_used_when_no_config() -> None:
    stages = resolve_stages(AttrPlugin, {})
    assert stages == [PipelineStage.DO]


def test_stage_falls_back_to_think() -> None:
    stages = resolve_stages(NoStagePlugin, {})
    assert stages == [PipelineStage.THINK]


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


@pytest.mark.asyncio
async def test_say_only_allowed_for_output() -> None:
    ctx = make_context(PipelineStage.PARSE)
    plugin = SayDuringParse({})
    with pytest.raises(PluginContextError):
        await plugin.execute(ctx)
