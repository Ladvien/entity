import asyncio
import pytest
from entity.core.resources.container import ResourceContainer
from entity.pipeline.errors import InitializationError
from entity.resources.logging import LoggingResource

from entity.pipeline.initializer import SystemInitializer


def test_initializer_fails_without_memory():
    cfg = {
        "plugins": {
            "agent_resources": {
                "llm": {"type": "entity.resources.llm:LLM"},
                "storage": {"type": "entity.resources.storage:Storage"},
                # metrics collector optional
            }
        },
        "workflow": {},
    }
    init = SystemInitializer(cfg)
    with pytest.raises(InitializationError, match="memory"):
        asyncio.run(init.initialize())


def test_initializer_fails_without_llm():
    cfg = {
        "plugins": {
            "agent_resources": {
                "memory": {"type": "entity.resources.memory:Memory"},
                "storage": {"type": "entity.resources.storage:Storage"},
            }
        },
        "workflow": {},
    }
    init = SystemInitializer(cfg)
    with pytest.raises(InitializationError, match="llm"):
        asyncio.run(init.initialize())


def test_initializer_fails_without_storage():
    cfg = {
        "plugins": {
            "agent_resources": {
                "memory": {"type": "entity.resources.memory:Memory"},
                "llm": {"type": "entity.resources.llm:LLM"},
            }
        },
        "workflow": {},
    }
    init = SystemInitializer(cfg)
    with pytest.raises(InitializationError, match="storage"):
        asyncio.run(init.initialize())


def test_initializer_succeeds_without_logging_config():
    cfg = {
        "plugins": {
            "agent_resources": {
                "memory": {"type": "entity.resources.memory:Memory"},
                "llm": {"type": "entity.resources.llm:LLM"},
                "storage": {"type": "entity.resources.storage:Storage"},
            }
        },
        "workflow": {},
    }
    init = SystemInitializer(cfg)
    asyncio.run(init.initialize())
    assert init.resource_container is not None
    assert init.resource_container.get("logging") is not None


def test_initializer_accepts_all_canonical_resources(monkeypatch):
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
            }
        },
        "workflow": {},
    }
    init = SystemInitializer(cfg)

    async def _noop(self) -> None:
        return None

    # Skip resource initialization complexity
    monkeypatch.setattr(ResourceContainer, "build_all", _noop)

    original_deps = LoggingResource.dependencies.copy()
    try:
        asyncio.run(init.initialize())
    finally:
        LoggingResource.dependencies = original_deps
