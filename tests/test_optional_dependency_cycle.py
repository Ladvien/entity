import pathlib
import sys

sys.path.insert(0, str(pathlib.Path("src").resolve()))

import yaml
import pytest

from entity.core.registry_validator import RegistryValidator
from entity.core.plugins import AgentResource
from entity.pipeline.errors import InitializationError
from entity.resources.logging import LoggingResource
from entity.resources.metrics import MetricsCollectorResource


class A(AgentResource):
    stages: list = []
    dependencies = ["b?"]

    async def _execute_impl(self, context):
        pass


A.dependencies = ["b?"]


class B(AgentResource):
    stages: list = []
    dependencies = ["a?"]

    async def _execute_impl(self, context):
        pass


B.dependencies = ["a?"]


def _write_config(tmp_path):
    path = tmp_path / "config.yaml"
    plugins = {
        "agent_resources": {
            "a": {"type": "tests.test_optional_dependency_cycle:A"},
            "b": {"type": "tests.test_optional_dependency_cycle:B"},
            "metrics_collector": {
                "type": "entity.resources.metrics:MetricsCollectorResource"
            },
            "logging": {"type": "entity.resources.logging:LoggingResource"},
        }
    }
    path.write_text(yaml.dump({"plugins": plugins}, sort_keys=False))
    return path


@pytest.mark.parametrize("patch_deps", [True])
def test_optional_cycle_detection(tmp_path, patch_deps):
    original_log_deps = LoggingResource.dependencies.copy()
    original_metrics_deps = MetricsCollectorResource.dependencies.copy()
    if patch_deps:
        LoggingResource.dependencies = []
        MetricsCollectorResource.dependencies = []
    try:
        config_path = _write_config(tmp_path)
        with pytest.raises(InitializationError, match="Circular dependency detected"):
            RegistryValidator(str(config_path)).run()
    finally:
        LoggingResource.dependencies = original_log_deps
        MetricsCollectorResource.dependencies = original_metrics_deps
