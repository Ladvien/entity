import yaml
import pytest

from entity.pipeline.initializer import SystemInitializer
from entity.core.plugins import PromptPlugin
from entity.core.resources.container import ResourceContainer
from entity.pipeline.stages import PipelineStage


class FirstPlugin(PromptPlugin):
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context):
        return "first"


class SecondPlugin(PromptPlugin):
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
    monkeypatch.setattr(SystemInitializer, "_discover_plugins", lambda self: None)

    async def _no_dep_validation(self, registry, dep_graph):
        return None

    monkeypatch.setattr(SystemInitializer, "_dependency_validation", _no_dep_validation)

    init = SystemInitializer.from_yaml(str(cfg_file))
    init._config_model.plugins.infrastructure.clear()
    init._config_model.plugins.resources.clear()
    init.config["plugins"]["infrastructure"] = {}
    init.config["plugins"]["resources"] = {}
    registry, container, tool_registry, workflow = await init.initialize()

    assert [p.__class__ for p in registry.list_plugins()] == [FirstPlugin, SecondPlugin]
    stage_plugins = registry.get_plugins_for_stage(str(PipelineStage.THINK))
    assert [p.__class__ for p in stage_plugins] == [FirstPlugin, SecondPlugin]
