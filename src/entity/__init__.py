"""Convenient access to the Entity agent and helpers."""

from __future__ import annotations

import asyncio

from .core.agent import Agent
from .core.registries import SystemRegistries
from .core.resources.container import ResourceContainer
from .core.runtime import AgentRuntime
from .core.stages import PipelineStage
from .infrastructure import DuckDBInfrastructure
from .resources import LLM, Memory, Storage
from .resources.interfaces.duckdb_vector_store import DuckDBVectorStore
from .resources.logging import LoggingResource
from .utils.setup_manager import Layer0SetupManager
from .workflows.minimal import minimal_workflow

__all__ = [
    "Agent",
    "PipelineStage",
    "SystemRegistries",
    "AgentRuntime",
    "ResourceContainer",
    "DuckDBInfrastructure",
    "LLM",
    "Memory",
    "Storage",
    "DuckDBVectorStore",
    "LoggingResource",
    "Layer0SetupManager",
    "minimal_workflow",
    "_create_default_agent",
]


def _create_default_agent() -> Agent:
    """Return a minimally configured default agent."""

    setup = Layer0SetupManager()
    try:
        asyncio.run(setup.setup())
    except Exception:
        pass

    agent = Agent()
    builder = agent.builder

    db = DuckDBInfrastructure({"path": str(setup.db_path)})
    vector_store = DuckDBVectorStore({})
    memory = Memory({})
    llm = LLM({})
    storage = Storage({})
    logging_res = LoggingResource({})

    llm.provider = None
    memory.database = db
    memory.vector_store = vector_store
    vector_store.database = db

    resources = ResourceContainer()

    async def init_resources() -> None:
        await db.initialize()
        await vector_store.initialize()
        await memory.initialize()
        await logging_res.initialize()

        await resources.add("database", db)
        await resources.add("vector_store", vector_store)
        await resources.add("llm", llm)
        await resources.add("memory", memory)
        await resources.add("storage", storage)
        await resources.add("logging", logging_res)

    asyncio.run(init_resources())

    caps = SystemRegistries(
        resources=resources,
        tools=builder.tool_registry,
        plugins=builder.plugin_registry,
    )
    agent._runtime = AgentRuntime(caps, workflow=minimal_workflow)
    return agent
