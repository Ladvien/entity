from entity.pipeline.initializer import SystemInitializer, ClassRegistry
from entity.core.plugins import (
    ToolPlugin,
    OutputAdapterPlugin,
    PromptPlugin,
)
from entity.core.stages import PipelineStage


class DummyTool(ToolPlugin):
    stages = [PipelineStage.DO]

    async def execute_function(self, params):
        return "ok"


DummyTool.dependencies = []


class DummyAdapter(OutputAdapterPlugin):
    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context):
        pass


DummyAdapter.dependencies = []


class DummyPrompt(PromptPlugin):
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context):
        pass


DummyPrompt.dependencies = []


def test_tool_dependencies_added():
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

    assert "metrics_collector?" in DummyTool.dependencies
    assert "logging" in DummyTool.dependencies


def _base_cfg() -> dict:
    return {
        "plugins": {
            "agent_resources": {
                "memory": {"type": "entity.resources.memory:Memory"},
                "llm": {"type": "entity.resources.llm:LLM"},
                "storage": {"type": "entity.resources.storage:Storage"},
                "logging": {"type": "entity.resources.logging:LoggingResource"},
                "metrics_collector": {
                    "type": "entity.resources.metrics:MetricsCollectorResource"
                },
            }
        },
        "workflow": {},
    }


def _base_cfg_no_metrics() -> dict:
    cfg = _base_cfg()
    cfg["plugins"]["agent_resources"].pop("metrics_collector")
    return cfg


def _base_cfg_no_logging() -> dict:
    cfg = _base_cfg()
    cfg["plugins"]["agent_resources"].pop("logging")
    return cfg


def test_adapter_dependencies_added():
    cfg = _base_cfg()
    cfg["plugins"]["adapters"] = {"dummy_adapter": {"type": f"{__name__}:DummyAdapter"}}

    init = SystemInitializer(cfg)
    registry = ClassRegistry()
    dep_graph: dict[str, list[str]] = {}
    init._register_plugins(registry, dep_graph)

    assert "metrics_collector?" in DummyAdapter.dependencies
    assert "logging" in DummyAdapter.dependencies


def test_prompt_dependencies_added():
    cfg = _base_cfg()
    cfg["plugins"]["prompts"] = {"dummy_prompt": {"type": f"{__name__}:DummyPrompt"}}

    init = SystemInitializer(cfg)
    registry = ClassRegistry()
    dep_graph: dict[str, list[str]] = {}
    init._register_plugins(registry, dep_graph)

    assert "metrics_collector?" in DummyPrompt.dependencies
    assert "logging" in DummyPrompt.dependencies


def test_dependencies_without_metrics():
    cfg = _base_cfg_no_metrics()
    cfg["plugins"]["tools"] = {"dummy": {"type": f"{__name__}:DummyTool"}}
    cfg["plugins"]["adapters"] = {"dummy_adapter": {"type": f"{__name__}:DummyAdapter"}}
    cfg["plugins"]["prompts"] = {"dummy_prompt": {"type": f"{__name__}:DummyPrompt"}}

    init = SystemInitializer(cfg)
    registry = ClassRegistry()
    dep_graph: dict[str, list[str]] = {}
    init._register_plugins(registry, dep_graph)

    assert "metrics_collector?" in DummyTool.dependencies
    assert "metrics_collector?" in DummyAdapter.dependencies
    assert "metrics_collector?" in DummyPrompt.dependencies


def test_dependencies_without_logging():
    cfg = _base_cfg_no_logging()
    cfg["plugins"]["tools"] = {"dummy": {"type": f"{__name__}:DummyTool"}}
    cfg["plugins"]["adapters"] = {"dummy_adapter": {"type": f"{__name__}:DummyAdapter"}}
    cfg["plugins"]["prompts"] = {"dummy_prompt": {"type": f"{__name__}:DummyPrompt"}}

    init = SystemInitializer(cfg)
    registry = ClassRegistry()
    dep_graph: dict[str, list[str]] = {}
    init._register_plugins(registry, dep_graph)

    assert "logging" in DummyTool.dependencies
    assert "logging" in DummyAdapter.dependencies
    assert "logging" in DummyPrompt.dependencies


def test_interface_resource_no_metrics_dependency() -> None:
    from entity.resources.interfaces.database import DatabaseResource
    from entity.resources.memory import Memory

    base_deps = DatabaseResource.dependencies.copy()
    mem_deps = Memory.dependencies.copy()
    DatabaseResource.dependencies = []
    Memory.dependencies = ["database", "vector_store?"]

    cfg = {
        "plugins": {
            "infrastructure": {
                "database_backend": {
                    "type": "entity.infrastructure.duckdb:DuckDBInfrastructure"
                }
            },
            "resources": {
                "database": {
                    "type": "entity.resources.interfaces.database:DatabaseResource"
                }
            },
            "agent_resources": {
                "memory": {"type": "entity.resources.memory:Memory"},
                "logging": {"type": "entity.resources.logging:LoggingResource"},
                "metrics_collector": {
                    "type": "entity.resources.metrics:MetricsCollectorResource"
                },
                "llm": {"type": "entity.resources.llm:LLM"},
                "storage": {"type": "entity.resources.storage:Storage"},
            },
        },
        "workflow": {},
    }

    init = SystemInitializer(cfg)
    registry = ClassRegistry()
    dep_graph: dict[str, list[str]] = {}
    init._register_plugins(registry, dep_graph)

    assert "metrics_collector?" not in DatabaseResource.dependencies
    assert "metrics_collector?" in Memory.dependencies

    DatabaseResource.dependencies = base_deps
    Memory.dependencies = mem_deps
