import asyncio

import yaml

from entity.core.agent import Agent
from pipeline import PipelineStage, PromptPlugin


class First(PromptPlugin):
    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context):
        order = context.get_metadata("order") or []
        order.append("first")
        context.set_metadata("order", order)
        _set_final_response(context)


class Second(PromptPlugin):
    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context):
        order = context.get_metadata("order") or []
        order.append("second")
        context.set_metadata("order", order)


class Third(PromptPlugin):
    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context):
        order = context.get_metadata("order") or []
        order.append("third")
        context.set_metadata("order", order)


def _set_final_response(context):
    order = context.get_metadata("order") or []
    context.set_response(order)


def test_agent_plugin_registration_order_matches_execution():
    agent = Agent()
    agent.add_plugin(First({}))
    agent.add_plugin(Third({}))
    agent.add_plugin(Second({}))
    agent._runtime = agent.builder.build_runtime()
    result = asyncio.run(agent.run_message("hi"))
    assert result == ["first", "third", "second"]


def test_agent_initializer_preserves_yaml_order(tmp_path):
    config = {
        "plugins": {
            "prompts": {
                "second": {
                    "type": "tests.test_core.test_core_plugin_registry_order:Second"
                },
                "first": {
                    "type": "tests.test_core.test_core_plugin_registry_order:First"
                },
                "third": {
                    "type": "tests.test_core.test_core_plugin_registry_order:Third"
                },
            }
        }
    }
    path = tmp_path / "config.yaml"
    path.write_text(yaml.dump(config))

    agent = Agent(config_path=str(path))
    asyncio.run(agent._ensure_runtime())
    plugins = agent.runtime.capabilities.plugins.get_plugins_for_stage(
        PipelineStage.OUTPUT
    )
    assert [p.__class__ for p in plugins] == [Second, First, Third]
