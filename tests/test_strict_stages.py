import pytest

from entity.pipeline.errors import InitializationError
from entity.pipeline.initializer import ClassRegistry, SystemInitializer
from entity.pipeline.stages import PipelineStage
from entity.core.plugins import PromptPlugin
from entity.resources.interfaces.database import DatabaseResource
from entity.resources.base import AgentResource as CanonicalResource  # noqa: F401


class DummyDB(DatabaseResource):
    async def _execute_impl(self, context):
        pass


class MyPlugin(PromptPlugin):
    stage = PipelineStage.DO

    async def _execute_impl(self, context):
        pass


import logging
from entity.utils.logging import configure_logging


def test_stage_mismatch_warning(caplog):
    cfg = {
        "plugins": {
            "agent_resources": {
                "memory": {"type": "entity.resources.memory:Memory"},
                "database": {"type": __name__ + ":DummyDB"},
                "llm": {"type": "entity.resources.llm:LLM"},
                "storage": {"type": "entity.resources.storage:Storage"},
            },
            "resources": {
                "logging": {"type": "entity.resources.logging:LoggingResource"},
                "metrics_collector": {
                    "type": "entity.resources.metrics:MetricsCollectorResource"
                },
            },
            "prompts": {"test": {"type": __name__ + ":MyPlugin", "stage": "think"}},
        },
        "workflow": {},
    }

    init = SystemInitializer(cfg)
    configure_logging("WARNING")
    registry = ClassRegistry()
    dep_graph: dict[str, list[str]] = {}
    init._register_plugins(registry, dep_graph)
    with caplog.at_level(logging.WARNING, logger="entity.pipeline.initializer"):
        init._warn_stage_mismatches(registry)
    assert any("override class stages" in r.message for r in caplog.records)


def test_stage_mismatch_strict():
    cfg = {
        "plugins": {
            "agent_resources": {
                "memory": {"type": "entity.resources.memory:Memory"},
                "database": {"type": __name__ + ":DummyDB"},
                "llm": {"type": "entity.resources.llm:LLM"},
                "storage": {"type": "entity.resources.storage:Storage"},
            },
            "resources": {
                "logging": {"type": "entity.resources.logging:LoggingResource"},
                "metrics_collector": {
                    "type": "entity.resources.metrics:MetricsCollectorResource"
                },
            },
            "prompts": {"test": {"type": __name__ + ":MyPlugin", "stage": "think"}},
        },
        "workflow": {},
    }

    init = SystemInitializer(cfg, strict_stages=True)
    configure_logging("WARNING")
    registry = ClassRegistry()
    dep_graph: dict[str, list[str]] = {}
    init._register_plugins(registry, dep_graph)
    with pytest.raises(InitializationError):
        init._warn_stage_mismatches(registry)
