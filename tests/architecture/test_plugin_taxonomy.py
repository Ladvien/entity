import yaml
import pytest

from entity.core.registry_validator import RegistryValidator
from entity.pipeline.initializer import SystemInitializer, InitializationError
from entity.core.plugins import (
    Plugin,
    AgentResource,
    InputAdapterPlugin,
    PromptPlugin,
)
from entity.core.stages import PipelineStage


class WrongResource(Plugin):
    stages: list = []

    async def _execute_impl(self, context):
        pass


class DummyResource(AgentResource):
    stages: list = []

    async def _execute_impl(self, context):
        pass


class BadDepPrompt(PromptPlugin):
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context):
        pass


class BadAdapter(InputAdapterPlugin):
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context):
        pass


class WrongPrompt(InputAdapterPlugin):
    stages = [PipelineStage.INPUT]

    async def _execute_impl(self, context):
        pass


def _write_cfg(tmp_path, plugins):
    cfg = {"plugins": plugins}
    path = tmp_path / "cfg.yaml"
    path.write_text(yaml.safe_dump(cfg))
    return path


def test_resource_base_validation(tmp_path):
    cfg = {
        "agent_resources": {
            "bad": {"type": "tests.architecture.test_plugin_taxonomy:WrongResource"},
            "metrics_collector": {
                "type": "entity.resources.metrics:MetricsCollectorResource"
            },
        }
    }
    path = _write_cfg(tmp_path, cfg)
    with pytest.raises(SystemError, match="ResourcePlugin"):
        RegistryValidator(str(path)).run()


def test_dependency_name_validation(tmp_path):
    cfg = {
        "agent_resources": {
            "dummy": {"type": "tests.architecture.test_plugin_taxonomy:DummyResource"},
            "metrics_collector": {
                "type": "entity.resources.metrics:MetricsCollectorResource"
            },
            "logging": {"type": "entity.resources.logging:LoggingResource"},
            "database": {
                "type": "tests.architecture.test_plugin_taxonomy:DummyResource"
            },
        },
        "prompts": {
            "bad": {
                "type": "tests.architecture.test_plugin_taxonomy:BadDepPrompt",
                "dependencies": ["missing"],
            }
        },
    }
    path = _write_cfg(tmp_path, cfg)
    with pytest.raises(SystemError, match="missing"):
        RegistryValidator(str(path)).run()


def test_stage_mismatch_validation(tmp_path):
    cfg = {
        "adapters": {
            "bad": {"type": "tests.architecture.test_plugin_taxonomy:BadAdapter"}
        }
    }
    path = _write_cfg(tmp_path, cfg)
    with pytest.raises(SystemError, match="INPUT stage"):
        RegistryValidator(str(path)).run()


def test_discovered_plugin_validation(tmp_path):
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    pyproject = plugin_dir / "pyproject.toml"
    pyproject.write_text(
        """
[tool.entity.plugins.prompts.bad]
type = "tests.architecture.test_plugin_taxonomy:WrongPrompt"
"""
    )
    initializer = SystemInitializer()
    initializer.config["plugin_dirs"] = [str(plugin_dir)]
    with pytest.raises(InitializationError, match="PromptPlugin"):
        initializer._discover_plugins()
