from entity.pipeline.initializer import SystemInitializer, ClassRegistry
from entity.core.plugins import ToolPlugin
from entity.core.stages import PipelineStage


class DummyTool(ToolPlugin):
    stages = [PipelineStage.DO]

    async def execute_function(self, params):
        return "ok"


DummyTool.dependencies = []


def test_register_plugins_appends_dependencies():
    cfg = {
        "plugins": {
            "agent_resources": {
                "memory": {"type": "entity.resources.memory:Memory"},
                "llm": {"type": "entity.resources.llm:LLM"},
                "storage": {"type": "entity.resources.storage:Storage"},
                "logging": {"type": "entity.resources.logging:LoggingResource"},
                "metrics_collector": {
                    "type": "entity.resources.metrics:MetricsCollectorResource"
                },
            },
            "tools": {"dummy": {"type": f"{__name__}:DummyTool"}},
        },
        "workflow": {},
    }

    init = SystemInitializer(cfg)
    registry = ClassRegistry()
    dep_graph: dict[str, list[str]] = {}
    init._register_plugins(registry, dep_graph)

    assert "metrics_collector" in DummyTool.dependencies
    assert "logging" in DummyTool.dependencies
