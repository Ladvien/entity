import yaml
import pytest
from pathlib import Path

from entity.core.agent import Agent
from entity.core.plugins import Plugin, ValidationResult
from entity.core.stages import PipelineStage
from entity.cli import EntityCLI
from entity.infrastructure import DuckDBInfrastructure
from entity.resources.database import DuckDBResource
from entity.resources.duckdb_vector_store import DuckDBVectorStore

from .test_reload_runtime_validation import run_reload


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
    await agent.add_plugin(plugin)
    agent.register_resource("database_backend", DuckDBInfrastructure, {}, layer=1)
    agent.register_resource("database", DuckDBResource, {}, layer=2)
    agent.register_resource("vector_store", DuckDBVectorStore, {}, layer=2)
    await agent.build_runtime()

    cli = EntityCLI.__new__(EntityCLI)
    cfg = {"plugins": {"prompts": {"unknown": {}}}}
    cfg_file = tmp_path / "reload.yaml"
    cfg_file.write_text(yaml.safe_dump(cfg))

    result = await run_reload(cli, agent, cfg_file)
    assert result == 2
