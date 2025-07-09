import asyncio

import yaml

from pipeline import (
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    SystemInitializer,
    SystemRegistries,
    ToolRegistry,
    execute_pipeline,
)
from entity.core.resources.container import ResourceContainer


class First(PromptPlugin):
    stages = [PipelineStage.DELIVER]

    async def _execute_impl(self, context):
        order = context.get_metadata("order") or []
        order.append("first")
        context.set_metadata("order", order)
        _set_final_response(context)


class Second(PromptPlugin):
    stages = [PipelineStage.DELIVER]

    async def _execute_impl(self, context):
        order = context.get_metadata("order") or []
        order.append("second")
        context.set_metadata("order", order)


class Third(PromptPlugin):
    stages = [PipelineStage.DELIVER]

    async def _execute_impl(self, context):
        order = context.get_metadata("order") or []
        order.append("third")
        context.set_metadata("order", order)


def _set_final_response(context):
    order = context.get_metadata("order") or []
    context.set_response(order)


def test_plugin_registration_order_matches_execution():
    registry = PluginRegistry()
    asyncio.run(registry.register_plugin_for_stage(First({}), PipelineStage.DELIVER))
    asyncio.run(registry.register_plugin_for_stage(Third({}), PipelineStage.DELIVER))
    asyncio.run(registry.register_plugin_for_stage(Second({}), PipelineStage.DELIVER))
    registries = SystemRegistries(ResourceContainer(), ToolRegistry(), registry)
    result = asyncio.run(execute_pipeline("hi", registries))
    assert result == ["first", "third", "second"]


def test_initializer_preserves_yaml_order(tmp_path):
    config = {
        "plugins": {
            "prompts": {
                "second": {"type": "tests.test_plugin_registry_order:Second"},
                "first": {"type": "tests.test_plugin_registry_order:First"},
                "third": {"type": "tests.test_plugin_registry_order:Third"},
            }
        }
    }
    path = tmp_path / "config.yaml"
    path.write_text(yaml.dump(config))

    initializer = SystemInitializer.from_yaml(str(path))
    plugin_reg, _, _ = asyncio.run(initializer.initialize())
    plugins = plugin_reg.get_plugins_for_stage(PipelineStage.DELIVER)
    assert [p.__class__ for p in plugins] == [Second, First, Third]
