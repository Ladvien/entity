import asyncio

from entity.core.resources.container import ResourceContainer
from entity.core.plugins import ResourcePlugin, PromptPlugin
from entity.core.stages import PipelineStage
from entity.core.registry_validator import RegistryValidator
import yaml


class OptionalRes(ResourcePlugin):
    stages = [PipelineStage.PARSE]

    async def _execute_impl(self, context):
        pass


class DependentRes(ResourcePlugin):
    stages = [PipelineStage.PARSE]
    dependencies = ["optional?"]

    def __init__(self, config=None):
        super().__init__(config or {})
        self.optional = "unset"

    async def _execute_impl(self, context):
        pass


class DummyPrompt(PromptPlugin):
    stages = [PipelineStage.DO]
    dependencies = ["missing?"]

    async def _execute_impl(self, context):
        pass


def test_missing_optional_dependency_sets_none():
    container = ResourceContainer()
    container.register("dependent", DependentRes, {})
    asyncio.run(container.build_all())
    dep = container.get("dependent")
    assert dep.optional is None


def test_present_optional_dependency_injected():
    container = ResourceContainer()
    container.register("optional", OptionalRes, {})
    container.register("dependent", DependentRes, {})
    asyncio.run(container.build_all())
    opt = container.get("optional")
    dep = container.get("dependent")
    assert dep.optional is opt


def test_registry_validator_allows_missing_optional(tmp_path):
    cfg = {
        "plugins": {
            "prompts": {
                "dummy": {"type": "tests.test_optional_dependencies:DummyPrompt"}
            }
        }
    }
    path = tmp_path / "cfg.yml"
    path.write_text(yaml.dump(cfg, sort_keys=False))
    RegistryValidator(str(path)).run()
