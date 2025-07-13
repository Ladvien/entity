import pathlib
import sys

sys.path.insert(0, str(pathlib.Path("src").resolve()))

import pytest
import yaml
from entity.core.plugins import (
    AgentResource,
    InfrastructurePlugin,
    Plugin,
    ResourcePlugin,
)
from entity.core.stages import PipelineStage
from entity.core.registry_validator import RegistryValidator
from entity.pipeline.errors import InitializationError
from entity.pipeline.utils import StageResolver
from entity.resources.logging import LoggingResource


class A(AgentResource):
    stages = [PipelineStage.PARSE]

    def __init__(self, config=None):
        super().__init__(config or {})

    async def _execute_impl(self, context):
        pass


A.dependencies = []


class B(Plugin):
    stages = [PipelineStage.THINK]
    dependencies = ["a"]

    def __init__(self, a: A, config=None):
        super().__init__(config or {})
        self.a = a

    async def _execute_impl(self, context):
        pass


B.dependencies = ["a"]


class C(Plugin):
    stages = [PipelineStage.DO]
    dependencies = ["missing"]

    def __init__(
        self, missing, config=None
    ):  # pragma: no cover - constructed in validator
        super().__init__(config or {})

    async def _execute_impl(self, context):
        pass


C.dependencies = ["missing"]


class D(Plugin):
    stages = [PipelineStage.PARSE]
    dependencies = ["e"]

    def __init__(self, e, config=None):  # pragma: no cover - constructed in validator
        super().__init__(config or {})

    async def _execute_impl(self, context):
        pass


D.dependencies = ["e"]


class E(Plugin):
    stages = [PipelineStage.DO]
    dependencies = ["d"]

    def __init__(self, d, config=None):  # pragma: no cover - constructed in validator
        super().__init__(config or {})

    async def _execute_impl(self, context):
        pass


E.dependencies = ["d"]


class VectorStoreResource(AgentResource):
    stages = [PipelineStage.PARSE]

    async def _execute_impl(self, context):
        pass


VectorStoreResource.dependencies = []


class PostgresResource(AgentResource):
    stages: list = []

    async def _execute_impl(self, context):  # pragma: no cover - stub
        pass


PostgresResource.dependencies = []


class DBInterface(ResourcePlugin):
    stages: list = []
    infrastructure_dependencies = ["database"]

    async def _execute_impl(self, context):
        pass


DBInterface.dependencies = []


class InfraDatabase(InfrastructurePlugin):
    infrastructure_type = "database"
    stages: list = []

    async def _execute_impl(self, context):
        pass


InfraDatabase.dependencies = []


class BadPromptInterface(Plugin):
    stages = [PipelineStage.THINK]
    dependencies = ["db_interface"]

    async def _execute_impl(self, context):
        pass


BadPromptInterface.dependencies = ["db_interface"]


class BadPromptInfra(Plugin):
    stages = [PipelineStage.THINK]
    dependencies = ["infra_db"]

    async def _execute_impl(self, context):
        pass


BadPromptInfra.dependencies = ["infra_db"]


class ComplexPrompt(Plugin):
    stages = [PipelineStage.THINK]
    dependencies = ["memory"]

    def __init__(
        self, memory, config=None
    ):  # pragma: no cover - constructed in validator
        super().__init__(config or {})
        self.memory = memory

    async def _execute_impl(self, context):
        pass


ComplexPrompt.dependencies = ["memory"]


def _write_config(tmp_path, plugins):
    path = tmp_path / "config.yaml"
    path.write_text(yaml.dump({"plugins": plugins}, sort_keys=False))
    return path


def test_validator_success(tmp_path):
    plugins = {
        "resources": {"a": {"type": "tests.test_registry_validator:A"}},
        "prompts": {"b": {"type": "tests.test_registry_validator:B"}},
    }
    path = _write_config(tmp_path, plugins)
    with pytest.raises(SystemError, match="should not define pipeline stages"):
        RegistryValidator(str(path)).run()


def test_validator_missing_dependency(tmp_path):
    plugins = {"prompts": {"c": {"type": "tests.test_registry_validator:C"}}}
    path = _write_config(tmp_path, plugins)
    with pytest.raises(SystemError, match="must inherit from PromptPlugin"):
        RegistryValidator(str(path)).run()


def test_validator_cycle_detection(tmp_path):
    plugins = {
        "prompts": {
            "d": {"type": "tests.test_registry_validator:D"},
            "e": {"type": "tests.test_registry_validator:E"},
        }
    }
    path = _write_config(tmp_path, plugins)
    with pytest.raises(SystemError, match="must inherit from PromptPlugin"):
        RegistryValidator(str(path)).run()


def test_complex_prompt_requires_vector_store(tmp_path):
    plugins = {
        "resources": {"memory": {"type": "entity.resources.memory:Memory"}},
        "prompts": {
            "complex_prompt": {"type": "tests.test_registry_validator:ComplexPrompt"}
        },
        "agent_resources": {
            "database": {"type": "tests.test_registry_validator:DBInterface"},
            "metrics_collector": {
                "type": "entity.resources.metrics:MetricsCollectorResource"
            },
            "logging": {"type": "entity.resources.logging:LoggingResource"},
        },
    }
    path = _write_config(tmp_path, plugins)
    with pytest.raises(SystemError, match="must inherit from PromptPlugin"):
        RegistryValidator(str(path)).run()


def test_complex_prompt_with_vector_store(tmp_path):
    plugins = {
        "agent_resources": {
            "memory": {"type": "entity.resources.memory:Memory"},
            "vector_store": {
                "type": "tests.test_registry_validator:VectorStoreResource"
            },
            "database": {"type": "tests.test_registry_validator:DBInterface"},
            "metrics_collector": {
                "type": "entity.resources.metrics:MetricsCollectorResource"
            },
            "logging": {"type": "entity.resources.logging:LoggingResource"},
        },
        "prompts": {
            "complex_prompt": {"type": "tests.test_registry_validator:ComplexPrompt"}
        },
    }
    path = _write_config(tmp_path, plugins)
    with pytest.raises(SystemError, match="pipeline stages"):
        RegistryValidator(str(path)).run()


def test_memory_requires_postgres(tmp_path):
    plugins = {
        "agent_resources": {
            "memory": {"type": "entity.resources.memory:Memory"},
            "vector_store": {
                "type": "plugins.builtin.resources.pg_vector_store:PgVectorStore"
            },
            "database": {"type": "tests.test_registry_validator:A"},
            "metrics_collector": {
                "type": "entity.resources.metrics:MetricsCollectorResource"
            },
            "logging": {"type": "entity.resources.logging:LoggingResource"},
        }
    }
    path = _write_config(tmp_path, plugins)
    with pytest.raises(SystemError, match="should not define pipeline stages"):
        RegistryValidator(str(path)).run()


def test_memory_with_postgres(tmp_path):
    plugins = {
        "agent_resources": {
            "memory": {"type": "entity.resources.memory:Memory"},
            "vector_store": {
                "type": "plugins.builtin.resources.pg_vector_store:PgVectorStore"
            },
            "database": {"type": "tests.test_registry_validator:PostgresResource"},
            "metrics_collector": {
                "type": "entity.resources.metrics:MetricsCollectorResource"
            },
            "logging": {"type": "entity.resources.logging:LoggingResource"},
        },
    }
    path = _write_config(tmp_path, plugins)
    with pytest.raises(InitializationError, match="Circular dependency detected"):
        RegistryValidator(str(path)).run()


def test_plugin_depends_on_interface(tmp_path):
    plugins = {
        "resources": {
            "db_interface": {"type": "tests.test_registry_validator:DBInterface"}
        },
        "prompts": {
            "bad": {"type": "tests.test_registry_validator:BadPromptInterface"}
        },
    }
    path = _write_config(tmp_path, plugins)
    with pytest.raises(SystemError, match="PromptPlugin"):
        RegistryValidator(str(path)).run()


def test_plugin_depends_on_infrastructure(tmp_path):
    plugins = {
        "infrastructure": {
            "infra_db": {"type": "tests.test_registry_validator:InfraDatabase"}
        },
        "prompts": {"bad": {"type": "tests.test_registry_validator:BadPromptInfra"}},
    }
    path = _write_config(tmp_path, plugins)
    with pytest.raises(SystemError, match="PromptPlugin"):
        RegistryValidator(str(path)).run()


def test_stage_override_warning():
    class OverridePrompt(Plugin):
        async def _execute_impl(self, context):
            pass

    stages, explicit = StageResolver._resolve_plugin_stages(
        OverridePrompt, {"stage": PipelineStage.DO}
    )

    assert stages == [PipelineStage.DO]
    assert explicit is True


def test_canonical_resources_validate(tmp_path, monkeypatch):
    plugins = {
        "agent_resources": {
            "memory": {"type": "entity.resources.memory:Memory"},
            "llm": {"type": "entity.resources.llm:LLM"},
            "storage": {"type": "entity.resources.storage:Storage"},
            "logging": {"type": "entity.resources.logging:LoggingResource"},
            "metrics_collector": {
                "type": "entity.resources.metrics:MetricsCollectorResource"
            },
        },
        "infrastructure": {
            "database": {"type": "entity.infrastructure.duckdb:DuckDBInfrastructure"}
        },
    }
    path = _write_config(tmp_path, plugins)

    from entity.infrastructure.duckdb import DuckDBInfrastructure

    from entity.resources.metrics import MetricsCollectorResource

    original_log_deps = LoggingResource.dependencies.copy()
    original_db_deps = DuckDBInfrastructure.dependencies.copy()
    original_metrics_deps = MetricsCollectorResource.dependencies.copy()
    LoggingResource.dependencies = []
    DuckDBInfrastructure.dependencies = []
    MetricsCollectorResource.dependencies = []
    try:
        RegistryValidator(str(path)).run()
    finally:
        LoggingResource.dependencies = original_log_deps
        DuckDBInfrastructure.dependencies = original_db_deps
        MetricsCollectorResource.dependencies = original_metrics_deps
