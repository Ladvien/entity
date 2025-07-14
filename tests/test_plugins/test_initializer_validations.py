import sys

import pytest

from entity.pipeline.initializer import SystemInitializer
from entity.pipeline.errors import InitializationError
from entity.core.plugins import PromptPlugin
from entity.pipeline.stages import PipelineStage
from entity.core.resources.container import ResourceContainer


class BadOutputPrompt(PromptPlugin):
    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context):
        pass


class MissingDepPrompt(PromptPlugin):
    dependencies = ["missing"]

    async def _execute_impl(self, context):
        pass


@pytest.mark.asyncio
async def test_output_stage_requires_output_adapter(monkeypatch):
    cfg = {
        "plugins": {"prompts": {"bad": {"type": f"{__name__}:BadOutputPrompt"}}},
        "workflow": {},
    }

    async def _noop(self) -> None:
        return None

    monkeypatch.setattr(ResourceContainer, "build_all", _noop)
    monkeypatch.setattr(
        SystemInitializer, "_ensure_canonical_resources", lambda self, container: None
    )
    init = SystemInitializer(cfg)
    with pytest.raises(InitializationError, match="OUTPUT stage"):
        await init.initialize()


@pytest.mark.asyncio
async def test_missing_dependency_name(monkeypatch):
    cfg = {
        "plugins": {
            "prompts": {
                "bad": {"type": f"{__name__}:MissingDepPrompt", "stage": "THINK"}
            }
        },
        "workflow": {},
    }

    async def _noop(self) -> None:
        return None

    monkeypatch.setattr(ResourceContainer, "build_all", _noop)
    monkeypatch.setattr(
        SystemInitializer, "_ensure_canonical_resources", lambda self, container: None
    )
    init = SystemInitializer(cfg)
    with pytest.raises(InitializationError, match="Missing dependency"):
        await init.initialize()


@pytest.mark.asyncio
async def test_discovery_checks_plugin_base(tmp_path, monkeypatch):
    plugin_dir = tmp_path / "plug"
    plugin_dir.mkdir()
    (plugin_dir / "__init__.py").write_text(
        "from entity.core.plugins import Plugin\nclass NotAResource(Plugin):\n    stages = []\n    dependencies = []\n    async def _execute_impl(self, context):\n        pass\n"
    )
    pyproject = plugin_dir / "pyproject.toml"
    pyproject.write_text(
        "[tool.entity.plugins.resources.bad]\n" "type = 'plug:NotAResource'\n"
    )

    sys.path.insert(0, str(tmp_path))

    cfg = {"plugins": {}, "workflow": {}}

    async def _noop(self) -> None:
        return None

    monkeypatch.setattr(ResourceContainer, "build_all", _noop)
    monkeypatch.setattr(
        SystemInitializer, "_ensure_canonical_resources", lambda self, container: None
    )
    init = SystemInitializer(cfg)
    init.config["plugin_dirs"] = [str(tmp_path)]
    with pytest.raises(InitializationError, match="ResourcePlugin"):
        await init.initialize()

    sys.path.remove(str(tmp_path))
