import asyncio

import yaml

from pipeline import (PipelineStage, PluginRegistry, PromptPlugin,
                      SystemInitializer, SystemRegistries, ToolRegistry,
                      execute_pipeline)
from pipeline.resources import ResourceContainer


class First(PromptPlugin):
    priority = 30
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        order = context.get_metadata("order") or []
        order.append("first")
        context.set_metadata("order", order)
        _set_final_response(context)


class Second(PromptPlugin):
    priority = 20
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        order = context.get_metadata("order") or []
        order.append("second")
        context.set_metadata("order", order)


class Third(PromptPlugin):
    priority = 10
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        order = context.get_metadata("order") or []
        order.append("third")
        context.set_metadata("order", order)


def _set_final_response(context):
    order = context.get_metadata("order") or []
    context.set_response(order)


def test_plugin_priority_order_matches_execution():
    registry = PluginRegistry()
    asyncio.run(registry.register_plugin_for_stage(First({}), PipelineStage.DO))
    asyncio.run(registry.register_plugin_for_stage(Third({}), PipelineStage.DO))
    asyncio.run(registry.register_plugin_for_stage(Second({}), PipelineStage.DO))
    registries = SystemRegistries(ResourceContainer(), ToolRegistry(), registry)
    result = asyncio.run(execute_pipeline("hi", registries))
    assert result == ["third", "second", "first"]


def test_initializer_orders_by_priority(tmp_path):
    config = {
        "plugins": {
            "prompts": {
                "second": {"type": "tests.test_plugin_registry_order:Second"},
                "first": {"type": "tests.test_plugin_registry_order:First"},
                "third": {"type": "tests.test_plugin_registry_order:Third"},
            }
        }
    }
    path = tmp_path / "config.yml"
    path.write_text(yaml.dump(config))

    initializer = SystemInitializer.from_yaml(str(path))
    plugin_reg, _, _ = asyncio.run(initializer.initialize())
    plugins = plugin_reg.get_plugins_for_stage(PipelineStage.DO)
    assert [p.__class__ for p in plugins] == [Third, Second, First]
