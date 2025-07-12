import asyncio
import yaml
import pytest
from pathlib import Path

from entity.core.agent import Agent
from entity.core.plugins import Plugin, ValidationResult
from entity.core.stages import PipelineStage
from entity.cli import EntityCLI


class SimplePlugin(Plugin):
    name = "simple"
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context):
        return "ok"

    @classmethod
    async def validate_config(cls, config):
        return ValidationResult(True, "")


@pytest.mark.asyncio
async def test_reload_requires_restart_when_plugin_missing(tmp_path: Path) -> None:
    agent = Agent()
    plugin = SimplePlugin({})
    await agent.builder.add_plugin(plugin)
    agent._runtime = await agent.builder.build_runtime()

    cli = EntityCLI.__new__(EntityCLI)
    cfg = {"plugins": {"prompts": {"unknown": {}}}}
    cfg_file = tmp_path / "reload.yaml"
    cfg_file.write_text(yaml.safe_dump(cfg))

    result = cli._reload_config(agent, str(cfg_file))
    assert result == 2
