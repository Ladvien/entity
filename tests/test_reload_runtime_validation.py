import asyncio
from pathlib import Path
import yaml
import pytest

from entity.core.agent import Agent
from entity.core.plugins import Plugin, ValidationResult
from entity.core.stages import PipelineStage
from entity.cli import EntityCLI
from entity.resources.logging import LoggingResource
from entity.resources.metrics import MetricsCollectorResource


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


class ReconfigPlugin(Plugin):
    name = "reconfiger"
    stages = [PipelineStage.THINK]

    def __init__(self, config):
        super().__init__(config)
        self.handled = False

    async def _execute_impl(self, context):
        return "ok"

    async def _handle_reconfiguration(self, old_config, new_config):
        self.handled = True


class FailingReconfigPlugin(Plugin):
    name = "badreconfig"
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context):
        return "ok"

    async def _handle_reconfiguration(self, old_config, new_config):
        raise RuntimeError("boom")


class DepPlugin(Plugin):
    name = "dep"
    stages = [PipelineStage.THINK]
    dependencies = ["reconfiger"]

    def __init__(self, cfg=None):
        super().__init__(cfg or {})
        self.notified = False

    async def _execute_impl(self, context):
        return "ok"

    async def on_dependency_reconfigured(self, name, old_config, new_config):
        self.notified = True
        return True


class RejectingDepPlugin(DepPlugin):
    async def on_dependency_reconfigured(self, name, old_config, new_config):
        self.notified = True
        return False


async def run_reload(cli: EntityCLI, agent: Agent, cfg_path: Path) -> int:
    return await asyncio.to_thread(cli._reload_config, agent, str(cfg_path))


@pytest.mark.asyncio
async def test_reload_aborts_on_failed_runtime_validation(tmp_path):
    agent = Agent()
    plugin = RuntimeCheckPlugin({"valid": True})
    await agent.add_plugin(plugin)
    LoggingResource.dependencies = []
    agent.register_resource("logging", LoggingResource, layer=2)
    await agent.build_runtime()

    # Ensure config updates do not call async validator
    async def _ok(cls, cfg):
        return ValidationResult(True, "")

    RuntimeCheckPlugin.validate_config = classmethod(_ok)

    cli = EntityCLI.__new__(EntityCLI)
    cfg = {
        "plugins": {"prompts": {"checker": {"valid": False}}},
        "runtime_validation_breaker": {"failure_threshold": 1},
    }
    cfg_file = tmp_path / "reload.yaml"
    cfg_file.write_text(yaml.safe_dump(cfg))

    result = await run_reload(cli, agent, cfg_file)
    assert result == 1


@pytest.mark.asyncio
async def test_reload_successful_reconfiguration(tmp_path):
    agent = Agent()
    plugin = ReconfigPlugin({"value": 1})
    await agent.add_plugin(plugin)
    LoggingResource.dependencies = []
    agent.register_resource("logging", LoggingResource, layer=2)
    await agent.build_runtime()

    async def _ok(cls, cfg):
        return ValidationResult(True, "")

    ReconfigPlugin.validate_config = classmethod(_ok)

    cli = EntityCLI.__new__(EntityCLI)
    cfg = {"plugins": {"prompts": {"reconfiger": {"value": 2}}}}
    cfg_file = tmp_path / "reload.yaml"
    cfg_file.write_text(yaml.safe_dump(cfg))

    result = await run_reload(cli, agent, cfg_file)
    assert result == 0
    assert plugin.config["value"] == 2
    assert plugin.config_version == 2
    assert plugin.handled


@pytest.mark.asyncio
async def test_reload_failed_reconfiguration(tmp_path):
    agent = Agent()
    plugin = FailingReconfigPlugin({"value": 1})
    await agent.add_plugin(plugin)
    LoggingResource.dependencies = []
    agent.register_resource("logging", LoggingResource, layer=2)
    await agent.build_runtime()

    async def _ok(cls, cfg):
        return ValidationResult(True, "")

    FailingReconfigPlugin.validate_config = classmethod(_ok)

    cli = EntityCLI.__new__(EntityCLI)
    cfg = {"plugins": {"prompts": {"badreconfig": {"value": 2}}}}
    cfg_file = tmp_path / "reload.yaml"
    cfg_file.write_text(yaml.safe_dump(cfg))

    result = await run_reload(cli, agent, cfg_file)
    assert result == 1
    assert plugin.config["value"] == 1
    assert plugin.config_version == 1


@pytest.mark.asyncio
async def test_reload_notifies_dependents(tmp_path):
    agent = Agent()
    plugin = ReconfigPlugin({"value": 1})
    dep = DepPlugin()
    await agent.add_plugin(plugin)
    await agent.add_plugin(dep)
    LoggingResource.dependencies = []
    agent.register_resource("logging", LoggingResource, layer=2)
    await agent.build_runtime()

    async def _ok(cls, cfg):
        return ValidationResult(True, "")

    ReconfigPlugin.validate_config = classmethod(_ok)
    DepPlugin.validate_config = classmethod(_ok)

    cli = EntityCLI.__new__(EntityCLI)
    cfg = {"plugins": {"prompts": {"reconfiger": {"value": 2}}}}
    cfg_file = tmp_path / "reload.yaml"
    cfg_file.write_text(yaml.safe_dump(cfg))

    result = await run_reload(cli, agent, cfg_file)
    assert result == 0
    assert plugin.config_version == 2
    assert dep.notified


@pytest.mark.asyncio
async def test_reload_rollback_on_dependency_rejection(tmp_path):
    agent = Agent()
    plugin = ReconfigPlugin({"value": 1})
    dep = RejectingDepPlugin()
    await agent.add_plugin(plugin)
    await agent.add_plugin(dep)
    LoggingResource.dependencies = []
    agent.register_resource("logging", LoggingResource, layer=2)
    await agent.build_runtime()

    async def _ok(cls, cfg):
        return ValidationResult(True, "")

    ReconfigPlugin.validate_config = classmethod(_ok)
    RejectingDepPlugin.validate_config = classmethod(_ok)

    cli = EntityCLI.__new__(EntityCLI)
    cfg = {"plugins": {"prompts": {"reconfiger": {"value": 2}}}}
    cfg_file = tmp_path / "reload.yaml"
    cfg_file.write_text(yaml.safe_dump(cfg))

    result = await run_reload(cli, agent, cfg_file)
    assert result == 1
    assert plugin.config_version == 1
    assert plugin.config["value"] == 1
    assert dep.notified
