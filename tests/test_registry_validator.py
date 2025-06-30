import pytest
import yaml

from pipeline.plugins import PromptPlugin, ResourcePlugin
from pipeline.stages import PipelineStage
from registry.validator import RegistryValidator


class A(ResourcePlugin):
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


class VectorMemoryResource(ResourcePlugin):
    stages = [PipelineStage.PARSE]

    async def _execute_impl(self, context):
        pass


class ComplexPrompt(PromptPlugin):
    stages = [PipelineStage.THINK]
    dependencies = ["vector_memory"]

    async def _execute_impl(self, context):
        pass


def _write_config(tmp_path, plugins):
    path = tmp_path / "config.yml"
    path.write_text(yaml.dump({"plugins": plugins}))
    return path


def test_validator_success(tmp_path):
    plugins = {
        "resources": {"a": {"type": "tests.test_registry_validator:A"}},
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


def test_complex_prompt_requires_vector_memory(tmp_path):
    plugins = {
        "prompts": {
            "complex_prompt": {"type": "tests.test_registry_validator:ComplexPrompt"}
        }
    }
    path = _write_config(tmp_path, plugins)
    with pytest.raises(SystemError, match="vector_memory"):
        RegistryValidator(str(path)).run()


def test_complex_prompt_with_vector_memory(tmp_path):
    plugins = {
        "resources": {
            "vector_memory": {
                "type": "tests.test_registry_validator:VectorMemoryResource"
            }
        },
        "prompts": {
            "complex_prompt": {"type": "tests.test_registry_validator:ComplexPrompt"}
        },
    }
    path = _write_config(tmp_path, plugins)
    RegistryValidator(str(path)).run()
