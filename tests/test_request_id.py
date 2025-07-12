from entity.core.resources.container import ResourceContainer
from entity.core.state import PipelineState
from pipeline import PluginRegistry, SystemRegistries, ToolRegistry
from entity.core.context import PluginContext


def make_context() -> PluginContext:
    state = PipelineState(conversation=[], pipeline_id="pid")
    registries = SystemRegistries(ResourceContainer(), ToolRegistry(), PluginRegistry())
    return PluginContext(state, registries)


def test_request_id_matches_pipeline_id():
    ctx = make_context()
    assert ctx.request_id == ctx.pipeline_id
