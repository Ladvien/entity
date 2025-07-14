import os

os.environ["ENTITY_AUTO_INIT"] = "0"

import entity
from entity.core.agent import Agent
from entity.pipeline.stages import PipelineStage


def _plugin_from(decorator, monkeypatch) -> entity.core.plugins.Plugin:
    ag = Agent()
    monkeypatch.setattr(entity, "_default_agent", ag, raising=False)

    @decorator
    async def dummy(context):
        pass

    return ag.builder._added_plugins[-1]


def test_input_decorator(monkeypatch):
    plugin = _plugin_from(entity.input, monkeypatch)
    assert plugin.stages == [PipelineStage.INPUT]


def test_parse_decorator(monkeypatch):
    plugin = _plugin_from(entity.parse, monkeypatch)
    assert plugin.stages == [PipelineStage.PARSE]


def test_prompt_decorator(monkeypatch):
    plugin = _plugin_from(entity.prompt, monkeypatch)
    assert plugin.stages == [PipelineStage.THINK]


def test_tool_decorator(monkeypatch):
    plugin = _plugin_from(entity.tool, monkeypatch)
    assert plugin.stages == [PipelineStage.DO]


def test_review_decorator(monkeypatch):
    plugin = _plugin_from(entity.review, monkeypatch)
    assert plugin.stages == [PipelineStage.REVIEW]


def test_output_decorator(monkeypatch):
    plugin = _plugin_from(entity.output, monkeypatch)
    assert plugin.stages == [PipelineStage.OUTPUT]


def test_plugin_multi_stage(monkeypatch):
    ag = Agent()
    monkeypatch.setattr(entity, "_default_agent", ag, raising=False)

    @entity.plugin(stages=[PipelineStage.INPUT, PipelineStage.PARSE])
    async def dummy(context):
        pass

    plugin = ag.builder._added_plugins[-1]
    assert plugin.stages == [PipelineStage.INPUT, PipelineStage.PARSE]
