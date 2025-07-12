import pathlib
import sys

sys.path.insert(0, str(pathlib.Path("src").resolve()))

from entity import agent
from entity.core.stages import PipelineStage
from entity import Agent


_DEFINITIONS = [
    (agent.input, PipelineStage.INPUT),
    (agent.parse, PipelineStage.PARSE),
    (agent.prompt, PipelineStage.THINK),
    (agent.tool, PipelineStage.DO),
    (agent.review, PipelineStage.REVIEW),
    (agent.output, PipelineStage.OUTPUT),
]


def _stage_of(decorator):
    _ = Agent()

    @decorator
    async def dummy(context):
        pass

    return dummy.__entity_plugin__.stages


for dec, stage in _DEFINITIONS:

    def _make_test(dec=dec, stage=stage):
        def test_func():
            assert _stage_of(dec) == [stage]

        return test_func

    globals()[f"test_{dec.__name__}_decorator"] = _make_test()


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
