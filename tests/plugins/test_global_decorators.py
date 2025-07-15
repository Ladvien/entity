import os

os.environ["ENTITY_AUTO_INIT"] = "0"

import entity
from entity.core.agent import Agent
from entity.pipeline.stages import PipelineStage


def _plugin_from(decorator) -> entity.core.plugins.Plugin:
    ag = Agent()
    old = entity._default_agent
    entity._default_agent = ag

    try:

        @decorator
        async def dummy(context):
            pass

    finally:
        entity._default_agent = old

    return ag.builder._added_plugins[-1]


def test_input_decorator():
    plugin = _plugin_from(entity.input)
    assert plugin.stages == [PipelineStage.INPUT]


def test_parse_decorator():
    plugin = _plugin_from(entity.parse)
    assert plugin.stages == [PipelineStage.PARSE]


def test_prompt_decorator():
    plugin = _plugin_from(entity.prompt)
    assert plugin.stages == [PipelineStage.THINK]


def test_tool_decorator():
    plugin = _plugin_from(entity.tool)
    assert plugin.stages == [PipelineStage.DO]


def test_review_decorator():
    plugin = _plugin_from(entity.review)
    assert plugin.stages == [PipelineStage.REVIEW]


def test_output_decorator():
    plugin = _plugin_from(entity.output)
    assert plugin.stages == [PipelineStage.OUTPUT]


def test_plugin_multi_stage():
    ag = Agent()
    old = entity._default_agent
    entity._default_agent = ag

    @entity.plugin(stages=[PipelineStage.INPUT, PipelineStage.PARSE])
    async def dummy(context):
        pass

    plugin = ag.builder._added_plugins[-1]
    entity._default_agent = old
    assert plugin.stages == [PipelineStage.INPUT, PipelineStage.PARSE]
