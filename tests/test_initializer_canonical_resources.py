import pathlib
import sys
import asyncio
import types
import pytest
from entity.core.resources.container import ResourceContainer
from pipeline.errors import InitializationError


sys.path.insert(0, str(pathlib.Path("src").resolve()))

from pipeline.initializer import SystemInitializer


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


def test_initializer_accepts_all_canonical_resources():
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

    async def _noop(self) -> None:
        return None

    # Skip resource initialization complexity
    ResourceContainer.build_all = types.MethodType(_noop, ResourceContainer)
    asyncio.run(init.initialize())
