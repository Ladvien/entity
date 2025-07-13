import yaml
import pytest

from entity.pipeline.initializer import SystemInitializer
from entity.core.plugins import Plugin
from entity.core.resources.container import ResourceContainer
from entity.pipeline.stages import PipelineStage


class FirstPlugin(Plugin):
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context):
        return "first"


class SecondPlugin(Plugin):
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context):
        return "second"


@pytest.mark.asyncio
async def test_plugin_order_preserved(tmp_path, monkeypatch):
    cfg = {
        "plugins": {
            "prompts": {
                "first": {"type": f"{__name__}:FirstPlugin"},
                "second": {"type": f"{__name__}:SecondPlugin"},
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
    registry, container, tool_registry, workflow = await init.initialize()

    assert [p.__class__ for p in registry.list_plugins()] == [FirstPlugin, SecondPlugin]
    stage_plugins = registry.get_plugins_for_stage(str(PipelineStage.THINK))
    assert [p.__class__ for p in stage_plugins] == [FirstPlugin, SecondPlugin]
