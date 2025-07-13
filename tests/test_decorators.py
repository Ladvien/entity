from __future__ import annotations

from entity import Agent
from entity.core import decorators
from entity.core.plugins import Plugin
from entity.core.stages import PipelineStage


def _plugin_from(decorator) -> Plugin:
    ag = Agent()

    @decorator
    async def dummy(context):
        pass

    import asyncio

    asyncio.run(ag.builder.add_plugin(dummy.__entity_plugin__))
    return ag.builder._added_plugins[-1]


def test_agent_input_decorator():
    plugin = _plugin_from(decorators.input)
    assert plugin.stages == [PipelineStage.INPUT]


def test_agent_parse_decorator():
    plugin = _plugin_from(decorators.parse)
    assert plugin.stages == [PipelineStage.PARSE]


def test_agent_prompt_decorator():
    plugin = _plugin_from(decorators.prompt)
    assert plugin.stages == [PipelineStage.THINK]


def test_agent_tool_decorator():
    plugin = _plugin_from(decorators.tool)
    assert plugin.stages == [PipelineStage.DO]


def test_agent_review_decorator():
    plugin = _plugin_from(decorators.review)
    assert plugin.stages == [PipelineStage.REVIEW]


def test_agent_output_decorator():
    plugin = _plugin_from(decorators.output)
    assert plugin.stages == [PipelineStage.OUTPUT]


def test_agent_tool_method_default_stage():
    ag = Agent()

    @ag.tool
    async def do_it(ctx):
        pass

    plugin = ag.builder._added_plugins[-1]
    assert plugin.stages == [PipelineStage.DO]


def test_agent_prompt_method_default_stage():
    ag = Agent()

    @ag.prompt
    async def think(ctx):
        pass

    plugin = ag.builder._added_plugins[-1]
    assert plugin.stages == [PipelineStage.THINK]
