import asyncio
from pathlib import Path
import yaml
import pytest

from entity.core.agent import Agent
from entity.core.plugins import Plugin, ValidationResult
from entity.core.stages import PipelineStage
from entity.cli import EntityCLI
from entity.core.registries import PluginRegistry
from entity.infrastructure import DuckDBInfrastructure
from entity.pipeline.config.config_update import update_plugin_configuration
from entity.resources.database import DuckDBResource
from entity.resources.duckdb_vector_store import DuckDBVectorStore


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


async def run_reload(cli: EntityCLI, agent: Agent, cfg_path: Path) -> int:
    return await asyncio.to_thread(cli._reload_config, agent, str(cfg_path))


@pytest.mark.asyncio
async def test_reload_aborts_on_failed_runtime_validation(tmp_path):
    agent = Agent()
    plugin = RuntimeCheckPlugin({"valid": True})
    await agent.add_plugin(plugin)
    agent.register_resource("database_backend", DuckDBInfrastructure, {}, layer=1)
    agent.register_resource("database", DuckDBResource, {}, layer=2)
    agent.register_resource("vector_store", DuckDBVectorStore, {}, layer=2)
    await agent.build_runtime()

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

    result = await run_reload(cli, agent, cfg_file)
    assert result == 1


@pytest.mark.asyncio
async def test_reload_successful_reconfiguration(tmp_path):
    agent = Agent()
    plugin = ReconfigPlugin({"value": 1})
    await agent.add_plugin(plugin)
    agent.register_resource("database_backend", DuckDBInfrastructure, {}, layer=1)
    agent.register_resource("database", DuckDBResource, {}, layer=2)
    agent.register_resource("vector_store", DuckDBVectorStore, {}, layer=2)
    await agent.build_runtime()

    ReconfigPlugin.validate_config = classmethod(
        lambda cls, cfg: ValidationResult(True, "")
    )

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
    agent.register_resource("database_backend", DuckDBInfrastructure, {}, layer=1)
    agent.register_resource("database", DuckDBResource, {}, layer=2)
    agent.register_resource("vector_store", DuckDBVectorStore, {}, layer=2)
    await agent.build_runtime()

    FailingReconfigPlugin.validate_config = classmethod(
        lambda cls, cfg: ValidationResult(True, "")
    )

    cli = EntityCLI.__new__(EntityCLI)
    cfg = {"plugins": {"prompts": {"badreconfig": {"value": 2}}}}
    cfg_file = tmp_path / "reload.yaml"
    cfg_file.write_text(yaml.safe_dump(cfg))

    result = await run_reload(cli, agent, cfg_file)
    assert result == 1
    assert plugin.config["value"] == 1
    assert plugin.config_version == 1


@pytest.mark.asyncio
async def test_invalid_config_keys_require_restart() -> None:
    registry = PluginRegistry()
    plugin = ReconfigPlugin({"value": 1})
    await registry.register_plugin_for_stage(
        plugin, str(PipelineStage.THINK), "reconfiger"
    )

    result = await update_plugin_configuration(
        registry, "reconfiger", {"value": 1, "extra": 5}
    )
    assert not result.success and result.requires_restart
    assert plugin.config_version == 1
