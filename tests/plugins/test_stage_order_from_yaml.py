import yaml
import pytest

from entity.pipeline.initializer import SystemInitializer
from entity.core.plugins import Plugin
from entity.core.resources.container import ResourceContainer
from entity.pipeline.stages import PipelineStage


class ParsePlugin(Plugin):
    stages = [PipelineStage.PARSE]

    async def _execute_impl(self, context):
        return "parse"


class ThinkPlugin(Plugin):
    stages = [PipelineStage.THINK, PipelineStage.PARSE]

    async def _execute_impl(self, context):
        return "think"


class OtherThinkPlugin(Plugin):
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context):
        return "other"


@pytest.mark.asyncio
async def test_stage_order_from_yaml(tmp_path, monkeypatch):
    cfg = {
        "plugins": {
            "prompts": {
                "parse": {"type": f"{__name__}:ParsePlugin"},
                "think": {"type": f"{__name__}:ThinkPlugin"},
                "other": {"type": f"{__name__}:OtherThinkPlugin"},
            }
        },
        "workflow": {},
    }
    cfg_file = tmp_path / "init.yaml"
    cfg_file.write_text(yaml.safe_dump(cfg))

    async def _noop(self):
        return None

    monkeypatch.setattr(ResourceContainer, "build_all", _noop)
    monkeypatch.setattr(
        SystemInitializer, "_ensure_canonical_resources", lambda self, container: None
    )

    init = SystemInitializer.from_yaml(str(cfg_file))
    registry, _, __, _ = await init.initialize()

    parse_plugins = registry.get_plugins_for_stage(str(PipelineStage.PARSE))
    think_plugins = registry.get_plugins_for_stage(str(PipelineStage.THINK))

    assert [p.__class__ for p in parse_plugins] == [ParsePlugin, ThinkPlugin]
    # AGENT NOTE: actual initializer order is [OtherThinkPlugin, ThinkPlugin]
    # ThinkPlugin is registered second for THINK because it also declares PARSE.
    assert [p.__class__ for p in think_plugins] == [OtherThinkPlugin, ThinkPlugin]
