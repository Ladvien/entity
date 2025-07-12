import logging

import pytest
import yaml
from entity.core.plugins import AgentResource, PromptPlugin
from entity.core.stages import PipelineStage
from entity.core.registry_validator import RegistryValidator
from pipeline.initializer import ClassRegistry


class A(AgentResource):
    stages = [PipelineStage.PARSE]

    async def _execute_impl(self, context):
        pass


class B(PromptPlugin):
    stages = [PipelineStage.THINK]
    dependencies = ["a"]

    async def _execute_impl(self, context):
        pass


class C(PromptPlugin):
    stages = [PipelineStage.DO]
    dependencies = ["missing"]

    async def _execute_impl(self, context):
        pass


class D(PromptPlugin):
    stages = [PipelineStage.PARSE]
    dependencies = ["e"]

    async def _execute_impl(self, context):
        pass


class E(PromptPlugin):
    stages = [PipelineStage.DO]
    dependencies = ["d"]

    async def _execute_impl(self, context):
        pass


class VectorStoreResource(AgentResource):
    stages = [PipelineStage.PARSE]

    async def _execute_impl(self, context):
        pass


class PostgresResource(AgentResource):
    stages: list = []

    async def _execute_impl(self, context):  # pragma: no cover - stub
        pass


class ComplexPrompt(PromptPlugin):
    stages = [PipelineStage.THINK]
    dependencies = ["memory"]

    async def _execute_impl(self, context):
        pass


def _write_config(tmp_path, plugins):
    path = tmp_path / "config.yaml"
    path.write_text(yaml.dump({"plugins": plugins}, sort_keys=False))
    return path


def test_validator_success(tmp_path):
    plugins = {
        "agent_resources": {"a": {"type": "tests.test_registry_validator:A"}},
        "prompts": {"b": {"type": "tests.test_registry_validator:B"}},
    }
    path = _write_config(tmp_path, plugins)
    RegistryValidator(str(path)).run()


def test_validator_missing_dependency(tmp_path):
    plugins = {"prompts": {"c": {"type": "tests.test_registry_validator:C"}}}
    path = _write_config(tmp_path, plugins)
    with pytest.raises(SystemError, match="requires 'missing'"):
        RegistryValidator(str(path)).run()


def test_validator_cycle_detection(tmp_path):
    plugins = {
        "prompts": {
            "d": {"type": "tests.test_registry_validator:D"},
            "e": {"type": "tests.test_registry_validator:E"},
        }
    }
    path = _write_config(tmp_path, plugins)
    with pytest.raises(SystemError, match="Circular dependency detected"):
        RegistryValidator(str(path)).run()


def test_complex_prompt_requires_vector_store(tmp_path):
    plugins = {
        "agent_resources": {"memory": {"type": "entity.resources.memory:Memory"}},
        "prompts": {
            "complex_prompt": {"type": "tests.test_registry_validator:ComplexPrompt"}
        },
    }
    path = _write_config(tmp_path, plugins)
    with pytest.raises(SystemError, match="vector store"):
        RegistryValidator(str(path)).run()


def test_complex_prompt_with_vector_store(tmp_path):
    plugins = {
        "agent_resources": {
            "memory": {
                "type": "entity.resources.memory:Memory",
                "vector_store": {
                    "type": "tests.test_registry_validator:VectorStoreResource"
                },
            }
        },
        "prompts": {
            "complex_prompt": {"type": "tests.test_registry_validator:ComplexPrompt"}
        },
    }
    path = _write_config(tmp_path, plugins)
    RegistryValidator(str(path)).run()


def test_memory_requires_postgres(tmp_path):
    plugins = {
        "agent_resources": {
            "memory": {
                "type": "entity.resources.memory:Memory",
                "vector_store": {
                    "type": "plugins.builtin.resources.pg_vector_store:PgVectorStore"
                },
            },
            "database": {"type": "tests.test_registry_validator:A"},
        }
    }
    path = _write_config(tmp_path, plugins)
    with pytest.raises(SystemError, match="vector store"):
        RegistryValidator(str(path)).run()


def test_memory_with_postgres(tmp_path):
    plugins = {
        "agent_resources": {
            "memory": {
                "type": "entity.resources.memory:Memory",
                "vector_store": {
                    "type": "plugins.builtin.resources.pg_vector_store:PgVectorStore"
                },
            },
            "database": {"type": "tests.test_registry_validator:PostgresResource"},
        },
    }
    path = _write_config(tmp_path, plugins)
    RegistryValidator(str(path)).run()


def test_stage_override_warning(caplog):
    class OverridePrompt(PromptPlugin):
        async def _execute_impl(self, context):
            pass

    registry = ClassRegistry()

    caplog.set_level(logging.WARNING, logger="pipeline.initializer")
    logging.getLogger("pipeline.initializer").addHandler(caplog.handler)
    registry._resolve_plugin_stages(OverridePrompt, {"stage": PipelineStage.DO})

    assert any(
        "override type defaults" in record.getMessage()
        and "OverridePrompt" in record.getMessage()
        for record in caplog.records
    )
