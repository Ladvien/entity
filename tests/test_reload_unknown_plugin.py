import yaml
from pathlib import Path

from entity.core.agent import Agent
from entity.core.builder import _AgentBuilder
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


def test_reload_requires_restart_when_plugin_missing(tmp_path: Path) -> None:
    builder = _AgentBuilder()
    plugin = SimplePlugin({})
    builder.add_plugin(plugin)
    runtime = builder.build_runtime()

    agent = Agent()
    agent._builder = builder
    agent._runtime = runtime

    cli = EntityCLI.__new__(EntityCLI)
    cfg = {"plugins": {"prompts": {"unknown": {}}}}
    cfg_file = tmp_path / "reload.yaml"
    cfg_file.write_text(yaml.safe_dump(cfg))

    result = cli._reload_config(agent, str(cfg_file))
    assert result == 2
