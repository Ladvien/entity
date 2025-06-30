import asyncio
import json
import os

import pytest
import yaml

from pipeline import (
    PipelineStage,
    PromptPlugin,
    ResourcePlugin,
    SystemInitializer,
    ValidationResult,
)


class A(ResourcePlugin):
    stages = [PipelineStage.PARSE]
    dependencies = []

    async def _execute_impl(self, context):
        pass

    async def initialize(self) -> None:
        self.initialized = True


class B(PromptPlugin):
    stages = [PipelineStage.THINK]
    dependencies = ["a"]

    async def _execute_impl(self, context):
        pass


class C(PromptPlugin):
    stages = [PipelineStage.THINK]
    dependencies = ["b"]

    async def _execute_impl(self, context):
        pass


class D(PromptPlugin):
    stages = [PipelineStage.THINK]
    dependencies: list[str] = []

    @classmethod
    def validate_dependencies(cls, registry):
        if not registry.has_plugin("a"):
            return ValidationResult.error_result("missing dependency 'a'")
        return ValidationResult.success_result()

    async def _execute_impl(self, context):
        pass


def test_initializer_env_and_dependencies(tmp_path):
    os.environ["TEST_VALUE"] = "ok"
    config = {
        "plugins": {
            "resources": {
                "a": {"type": "tests.test_initializer:A", "val": "${TEST_VALUE}"}
            },
            "prompts": {
                "b": {"type": "tests.test_initializer:B"},
                "c": {"type": "tests.test_initializer:C"},
            },
        }
    }
    path = tmp_path / "config.yml"
    path.write_text(yaml.dump(config))

    initializer = SystemInitializer.from_yaml(str(path))
    assert initializer.get_resource_config("a")["val"] == "ok"

    plugin_reg, resource_reg, tool_reg = asyncio.run(initializer.initialize())

    assert resource_reg.get("A") or resource_reg.get("a")
    think_plugins = plugin_reg.get_for_stage(PipelineStage.THINK)
    assert len(think_plugins) == 2


def test_validate_dependencies_missing(tmp_path):
    config = {"plugins": {"prompts": {"d": {"type": "tests.test_initializer:D"}}}}
    path = tmp_path / "config.yml"
    path.write_text(yaml.dump(config))

    initializer = SystemInitializer.from_yaml(str(path))
    with pytest.raises(SystemError, match="missing dependency 'a'"):
        asyncio.run(initializer.initialize())


def test_initializer_from_json_and_dict(tmp_path):
    config = {
        "plugins": {
            "resources": {
                "a": {"type": "tests.test_initializer:A"},
            },
            "prompts": {
                "b": {"type": "tests.test_initializer:B"},
            },
        }
    }

    yaml_path = tmp_path / "cfg.yml"
    json_path = tmp_path / "cfg.json"
    yaml_path.write_text(yaml.dump(config))
    json_path.write_text(json.dumps(config))

    init_yaml = SystemInitializer.from_yaml(str(yaml_path))
    init_json = SystemInitializer.from_json(str(json_path))
    init_dict = SystemInitializer.from_dict(config)

    assert init_yaml.config == init_json.config == init_dict.config

    py, ry, _ = asyncio.run(init_yaml.initialize())
    pj, rj, _ = asyncio.run(init_json.initialize())
    pd, rd, _ = asyncio.run(init_dict.initialize())

    assert (
        len(py.get_for_stage(PipelineStage.THINK))
        == len(pj.get_for_stage(PipelineStage.THINK))
        == len(pd.get_for_stage(PipelineStage.THINK))
    )
    assert ry.get("A") and rj.get("A") and rd.get("A")
