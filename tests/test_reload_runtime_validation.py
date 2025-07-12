import asyncio
from pathlib import Path
import yaml

from entity.core.agent import Agent
from entity.core.builder import _AgentBuilder
from entity.core.plugins import Plugin, ValidationResult
from entity.core.stages import PipelineStage
from entity.cli import EntityCLI


class RuntimeCheckPlugin(Plugin):
    name = "checker"
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context):
        return "ok"

    async def validate_runtime(self) -> ValidationResult:
        if not self.config.get("valid", True):
            return ValidationResult(False, "runtime failed")
        return ValidationResult(True, "")

    pass


async def run_reload(cli: EntityCLI, agent: Agent, cfg_path: Path) -> int:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, cli._reload_config, agent, str(cfg_path))


def test_reload_aborts_on_failed_runtime_validation(tmp_path):
    builder = _AgentBuilder()
    plugin = RuntimeCheckPlugin({"valid": True})
    builder.add_plugin(plugin)
    runtime = builder.build_runtime()

    agent = Agent()
    agent._builder = builder
    agent._runtime = runtime

    # Ensure config updates do not call async validator
    RuntimeCheckPlugin.validate_config = classmethod(
        lambda cls, cfg: ValidationResult(True, "")
    )

    cli = EntityCLI.__new__(EntityCLI)
    cfg = {
        "plugins": {"prompts": {"checker": {"valid": False}}},
        "runtime_validation_breaker": {"failure_threshold": 1},
    }
    cfg_file = tmp_path / "reload.yaml"
    cfg_file.write_text(yaml.safe_dump(cfg))

    result = cli._reload_config(agent, str(cfg_file))
    assert result == 1
