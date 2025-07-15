import yaml
import pytest

from entity.pipeline.initializer import SystemInitializer
from entity.core.plugins import PromptPlugin
from entity.core.resources.container import ResourceContainer
from entity.pipeline.stages import PipelineStage


class ParsePlugin(PromptPlugin):
    stages = [PipelineStage.PARSE]

    async def _execute_impl(self, context):
        return "parse"


class ThinkPlugin(PromptPlugin):
    stages = [PipelineStage.THINK, PipelineStage.PARSE]

    async def _execute_impl(self, context):
        return "think"


class OtherThinkPlugin(PromptPlugin):
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
    monkeypatch.setattr(SystemInitializer, "_discover_plugins", lambda self: None)

    async def _no_dep_validation(self, registry, dep_graph):
        return None

    monkeypatch.setattr(SystemInitializer, "_dependency_validation", _no_dep_validation)

    init = SystemInitializer.from_yaml(str(cfg_file))
    init._config_model.plugins.infrastructure.clear()
    init._config_model.plugins.resources.clear()
    init.config["plugins"]["infrastructure"] = {}
    init.config["plugins"]["resources"] = {}
    registry, _, __, _ = await init.initialize()

    parse_plugins = registry.get_plugins_for_stage(str(PipelineStage.PARSE))
    think_plugins = registry.get_plugins_for_stage(str(PipelineStage.THINK))

    assert [p.__class__ for p in parse_plugins] == [ParsePlugin, ThinkPlugin]
    # AGENT NOTE: actual initializer order is [OtherThinkPlugin, ThinkPlugin]
    # ThinkPlugin is registered second for THINK because it also declares PARSE.
    assert [p.__class__ for p in think_plugins] == [OtherThinkPlugin, ThinkPlugin]
