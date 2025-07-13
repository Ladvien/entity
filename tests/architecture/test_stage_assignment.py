from entity.core.plugins import Plugin
from entity.pipeline.utils import resolve_stages
from entity.core.stages import PipelineStage


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
