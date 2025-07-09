import asyncio

import pytest
import yaml
from pipeline import (PipelineStage, PromptPlugin, ResourcePlugin,
                      SystemInitializer, ValidationResult)


class ValidatingPlugin(PromptPlugin):
    stages = [PipelineStage.DO]

    @classmethod
    def validate_config(cls, config):
        if "required" not in config:
            return ValidationResult.error_result("missing 'required'")
        return ValidationResult.success_result()

    async def _execute_impl(self, context):
        pass


class DepPlugin(PromptPlugin):
    stages = [PipelineStage.DO]
    dependencies = ["resource"]

    async def _execute_impl(self, context):
        pass


class Res(ResourcePlugin):
    stages = [PipelineStage.PARSE]

    async def _execute_impl(self, context):
        pass


def test_from_dict_validation():
    with pytest.raises(Exception):
        ValidatingPlugin.from_dict({})
    plugin = ValidatingPlugin.from_dict({"required": True})
    assert isinstance(plugin, ValidatingPlugin)


def test_dependency_validation(tmp_path):
    cfg = {
        "plugins": {
            "prompts": {"dep": {"type": "tests.test_validation:DepPlugin"}},
        }
    }
    path = tmp_path / "cfg.yml"
    path.write_text(yaml.dump(cfg))
    initializer = SystemInitializer.from_yaml(str(path))
    with pytest.raises(SystemError):
        asyncio.run(initializer.initialize())

    cfg["plugins"]["resources"] = {"resource": {"type": "tests.test_validation:Res"}}
    path.write_text(yaml.dump(cfg))
    initializer = SystemInitializer.from_yaml(str(path))
    registries = asyncio.run(initializer.initialize())
    assert registries[2] is not None
