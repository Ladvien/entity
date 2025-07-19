import pytest
from entity.core.context import PluginContext
from entity.core.plugins import Plugin, PromptPlugin
from entity.core.stages import PipelineStage
from entity.pipeline.errors import PluginContextError
from entity.pipeline.utils import resolve_stages
from tests.utils import make_async_context


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


@pytest.mark.asyncio
async def test_say_only_allowed_for_output() -> None:
    ctx = await make_async_context(stage=PipelineStage.PARSE)
    plugin = SayDuringParse({})
    with pytest.raises(PluginContextError):
        await plugin.execute(ctx)
