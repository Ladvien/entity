import yaml
from entity.cli import EntityCLI
from entity.core.plugins import Plugin, AgentResource, ValidationResult
from pipeline.stages import PipelineStage


class DummyResource(AgentResource):
    stages: list = []

    async def _execute_impl(self, context):
        return None

    async def validate_runtime(self, breaker):
        return ValidationResult.success_result()


class FailingRuntimeResource(AgentResource):
    stages: list = []

    async def _execute_impl(self, context):
        return None

    async def validate_runtime(self, breaker):
        return ValidationResult.error_result("runtime failed")


class BadConfigPlugin(Plugin):
    stages = [PipelineStage.THINK]

    @classmethod
    async def validate_config(cls, config):
        return ValidationResult.error_result("invalid")

    async def _execute_impl(self, context):
        return "ok"


class BadDepPlugin(Plugin):
    stages = [PipelineStage.THINK]

    @classmethod
    async def validate_dependencies(cls, registry):
        return ValidationResult.error_result("missing")

    async def _execute_impl(self, context):
        return "ok"


def _write_config(tmp_path, plugins, resources, breaker=None):
    cfg = {
        "plugins": {
            "agent_resources": resources,
            "prompts": plugins,
        },
        "workflow": {},
    }
    if breaker:
        cfg["runtime_validation_breaker"] = breaker
    path = tmp_path / "cfg.yaml"
    path.write_text(yaml.safe_dump(cfg))
    return path


def _base_resources(resource_cls):
    return {
        "memory": {"type": f"tests.test_cli_validate_failures:{resource_cls.__name__}"},
        "llm": {"type": "tests.test_cli_validate_failures:DummyResource"},
        "storage": {"type": "tests.test_cli_validate_failures:DummyResource"},
    }


def test_validate_config_failure(tmp_path):
    cfg_path = _write_config(
        tmp_path,
        {"bad": {"type": "tests.test_cli_validate_failures:BadConfigPlugin"}},
        _base_resources(DummyResource),
    )
    cli = EntityCLI.__new__(EntityCLI)
    result = cli._validate_config(str(cfg_path))
    assert result == 1


def test_validate_dependency_failure(tmp_path):
    cfg_path = _write_config(
        tmp_path,
        {"bad": {"type": "tests.test_cli_validate_failures:BadDepPlugin"}},
        _base_resources(DummyResource),
    )
    cli = EntityCLI.__new__(EntityCLI)
    result = cli._validate_config(str(cfg_path))
    assert result == 1


def test_runtime_breaker_trips(tmp_path):
    cfg_path = _write_config(
        tmp_path,
        {},
        _base_resources(FailingRuntimeResource),
        breaker={"failure_threshold": 1},
    )
    cli = EntityCLI.__new__(EntityCLI)
    result = cli._validate_config(str(cfg_path))
    assert result == 1
