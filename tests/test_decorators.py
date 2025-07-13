import pathlib
import sys

sys.path.insert(0, str(pathlib.Path("src").resolve()))

from entity import Agent, agent
from entity.core.stages import PipelineStage


def _plugin_for(decorator):
    @decorator
    async def dummy(context):
        pass

    return agent.builder._added_plugins.pop()


def test_input_decorator():
    plugin = _plugin_for(agent.input)
    assert plugin.stages == [PipelineStage.INPUT]


def test_parse_decorator():
    plugin = _plugin_for(agent.parse)
    assert plugin.stages == [PipelineStage.PARSE]


def test_prompt_decorator():
    plugin = _plugin_for(agent.prompt)
    assert plugin.stages == [PipelineStage.THINK]


def test_tool_decorator():
    plugin = _plugin_for(agent.tool)
    assert plugin.stages == [PipelineStage.DO]


def test_review_decorator():
    plugin = _plugin_for(agent.review)
    assert plugin.stages == [PipelineStage.REVIEW]


def test_output_decorator():
    plugin = _plugin_for(agent.output)
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
