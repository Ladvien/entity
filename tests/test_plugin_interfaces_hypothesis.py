from hypothesis import given
from hypothesis import strategies as st

from pipeline import PipelineStage
from pipeline.interfaces import PluginAutoClassifier


@given(st.sampled_from([s.name for s in PipelineStage]))
def test_classifier_respects_stage_hint(stage_name: str) -> None:
    async def dummy(ctx):
        return "ok"

    plugin = PluginAutoClassifier.classify(dummy, {"stage": stage_name})
    assert plugin.stages == [PipelineStage.from_str(stage_name)]


@given(st.text(min_size=1, max_size=20))
def test_classifier_assigns_name(name: str) -> None:
    async def dummy(ctx):
        return "ok"

    plugin = PluginAutoClassifier.classify(dummy, {"name": name})
    assert plugin.name == name
