import pathlib
import sys

sys.path.insert(0, str(pathlib.Path("src").resolve()))

from entity import agent
from entity.core.stages import PipelineStage
from entity import Agent
import pytest


_DEFINITIONS = [
    (agent.input, PipelineStage.INPUT),
    (agent.parse, PipelineStage.PARSE),
    (agent.prompt, PipelineStage.THINK),
    (agent.tool, PipelineStage.DO),
    (agent.review, PipelineStage.REVIEW),
    (agent.output, PipelineStage.OUTPUT),
]


@pytest.mark.parametrize("decorator, stage", _DEFINITIONS)
def test_agent_decorator_adds_stage(decorator, stage):
    ag = Agent()
    bound = getattr(ag, decorator.__name__)

    @bound
    async def dummy(context):
        pass

    plugin = ag.builder._added_plugins[-1]
    assert plugin.stages == [stage]


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
