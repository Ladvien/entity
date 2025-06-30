import asyncio

import yaml

from pipeline import (
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    ResourceRegistry,
    SystemInitializer,
    SystemRegistries,
    ToolRegistry,
    execute_pipeline,
)


class First(PromptPlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        context.set_metadata("order", ["first"])


class Second(PromptPlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        order = context.get_metadata("order")
        order.append("second")
        context.set_metadata("order", order)


class Third(PromptPlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        order = context.get_metadata("order")
        order.append("third")
        context.set_metadata("order", order)
        context.set_response(order)


def test_plugin_registration_order_matches_execution():
    registry = PluginRegistry()
    registry.register_plugin_for_stage(First({}), PipelineStage.DO)
    registry.register_plugin_for_stage(Second({}), PipelineStage.DO)
    registry.register_plugin_for_stage(Third({}), PipelineStage.DO)
    registries = SystemRegistries(ResourceRegistry(), ToolRegistry(), registry)
    result = asyncio.run(execute_pipeline("hi", registries))
    assert result == ["first", "second", "third"]


def test_initializer_preserves_yaml_order(tmp_path):
    config = {
        "plugins": {
            "prompts": {
                "first": {"type": "tests.test_plugin_registry_order:First"},
                "second": {"type": "tests.test_plugin_registry_order:Second"},
                "third": {"type": "tests.test_plugin_registry_order:Third"},
            }
        }
    }
    path = tmp_path / "config.yml"
    path.write_text(yaml.dump(config))

    initializer = SystemInitializer.from_yaml(str(path))
    plugin_reg, _, _ = asyncio.run(initializer.initialize())
    plugins = plugin_reg.get_for_stage(PipelineStage.DO)
    assert [p.__class__ for p in plugins] == [First, Second, Third]
