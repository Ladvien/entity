"""Simplified package initializer for tests."""

from __future__ import annotations

import asyncio
from typing import Optional

from .core.agent import Agent
from .core.plugins import PromptPlugin, ToolPlugin
from .core.registries import SystemRegistries
from .core.resources.container import ResourceContainer
from .core.runtime import AgentRuntime
from .core.stages import PipelineStage
from .infrastructure.duckdb import DuckDBInfrastructure
from .resources import LLM, Memory, Storage
from .resources.interfaces.duckdb_vector_store import DuckDBVectorStore
from .resources.logging import LoggingResource
from .utils.setup_manager import Layer0SetupManager
from .workflows.minimal import minimal_workflow

__all__ = [
    "Agent",
    "PromptPlugin",
    "ToolPlugin",
    "ResourceContainer",
    "SystemRegistries",
    "AgentRuntime",
    "PipelineStage",
    "DuckDBInfrastructure",
    "LLM",
    "Memory",
    "Storage",
    "LoggingResource",
    "DuckDBVectorStore",
    "Layer0SetupManager",
    "minimal_workflow",
    "_create_default_agent",
    "plugin",
]

_default_agent: Optional[Agent] = None


def _create_default_agent() -> Agent:
    """Return a basic Agent with default resources."""
    setup = Layer0SetupManager()
    asyncio.run(setup.setup())
    agent = Agent()
    db = DuckDBInfrastructure({"path": str(setup.db_path)})
    llm = LLM({})
    vector_store = DuckDBVectorStore({})
    memory = Memory({})
    storage = Storage({})
    logging_res = LoggingResource({})
    llm.provider = None
    memory.database = db
    vector_store.database = db
    memory.vector_store = vector_store

    resources = ResourceContainer()
    asyncio.run(resources.add("database", db))
    asyncio.run(resources.add("vector_store", vector_store))
    asyncio.run(resources.add("llm", llm))
    asyncio.run(resources.add("memory", memory))
    asyncio.run(resources.add("storage", storage))
    asyncio.run(resources.add("logging", logging_res))

    agent._runtime = AgentRuntime(
        SystemRegistries(resources=resources), workflow=minimal_workflow
    )
    return agent


def _ensure_agent() -> Agent:
    global _default_agent
    if _default_agent is None:
        _default_agent = _create_default_agent()
    return _default_agent


agent = _ensure_agent()
plugin = agent.plugin
