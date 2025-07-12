import pathlib
import sys
import asyncio
import pytest
from entity.core.resources.container import ResourceContainer
from entity.pipeline.errors import InitializationError
from entity.core.plugins import ValidationResult
from entity.resources.interfaces.database import DatabaseResource


sys.path.insert(0, str(pathlib.Path("src").resolve()))

from entity.pipeline.initializer import SystemInitializer


class DummyDatabase(DatabaseResource):
    infrastructure_dependencies: list[str] = []

    async def connection(self):
        yield None

    @classmethod
    async def validate_dependencies(cls, registry):
        return ValidationResult.success_result()


def _base_config() -> dict:
    return {
        "plugins": {
            "resources": {
                "database": {
                    "type": "tests.test_initializer_canonical_resources:DummyDatabase"
                },
                "llm_provider": {
                    "type": "plugins.builtin.resources.echo_llm:EchoLLMResource"
                },
            },
            "agent_resources": {},
        },
        "workflow": {},
    }


def test_initializer_fails_without_memory():
    cfg = _base_config()
    cfg["plugins"]["agent_resources"] = {
        "llm": {"type": "entity.resources.llm:LLM"},
        "storage": {"type": "entity.resources.storage:Storage"},
    }
    init = SystemInitializer(cfg)
    with pytest.raises(InitializationError, match="memory"):
        asyncio.run(init.initialize())


def test_initializer_fails_without_llm():
    cfg = _base_config()
    cfg["plugins"]["agent_resources"] = {
        "memory": {"type": "entity.resources.memory:Memory"},
        "storage": {"type": "entity.resources.storage:Storage"},
    }
    init = SystemInitializer(cfg)
    with pytest.raises(InitializationError, match="llm"):
        asyncio.run(init.initialize())


def test_initializer_fails_without_storage():
    cfg = _base_config()
    cfg["plugins"]["agent_resources"] = {
        "memory": {"type": "entity.resources.memory:Memory"},
        "llm": {"type": "entity.resources.llm:LLM"},
    }
    init = SystemInitializer(cfg)
    with pytest.raises(InitializationError, match="storage"):
        asyncio.run(init.initialize())


def test_initializer_fails_without_logging():
    cfg = _base_config()
    cfg["plugins"]["agent_resources"] = {
        "memory": {"type": "entity.resources.memory:Memory"},
        "llm": {"type": "entity.resources.llm:LLM"},
        "storage": {"type": "entity.resources.storage:Storage"},
    }
    init = SystemInitializer(cfg)
    with pytest.raises(InitializationError, match="logging"):
        asyncio.run(init.initialize())


def test_initializer_accepts_all_canonical_resources(monkeypatch):
    cfg = _base_config()
    cfg["plugins"]["agent_resources"] = {
        "memory": {"type": "entity.resources.memory:Memory"},
        "llm": {"type": "entity.resources.llm:LLM"},
        "storage": {"type": "entity.resources.storage:Storage"},
        "logging": {"type": "entity.resources.logging:LoggingResource"},
    }
    init = SystemInitializer(cfg)

    async def _noop(self) -> None:
        return None

    # Skip resource initialization complexity and dependency validation
    monkeypatch.setattr(ResourceContainer, "build_all", _noop)
    monkeypatch.setattr(
        SystemInitializer, "_validate_dependency_graph", lambda *a, **k: None
    )
    asyncio.run(init.initialize())
