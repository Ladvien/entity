import asyncio
import os
import tempfile

import yaml

from pipeline import PipelineStage, PromptPlugin, ResourcePlugin, SystemInitializer


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
