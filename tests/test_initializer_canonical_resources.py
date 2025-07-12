import pathlib
import sys
import asyncio
import types
import pytest
from entity.core.resources.container import ResourceContainer
from entity.pipeline.errors import InitializationError


sys.path.insert(0, str(pathlib.Path("src").resolve()))

from entity.pipeline.initializer import SystemInitializer


def test_initializer_fails_without_memory():
    cfg = {
        "plugins": {
            "agent_resources": {
                "llm": {"type": "entity.resources.llm:LLM"},
                "storage": {"type": "entity.resources.storage:Storage"},
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


def test_initializer_fails_without_logging():
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
            }
        },
        "workflow": {},
    }
    init = SystemInitializer(cfg)

    async def _noop(self) -> None:
        return None

    # Skip resource initialization complexity
    monkeypatch.setattr(ResourceContainer, "build_all", _noop)
    asyncio.run(init.initialize())
