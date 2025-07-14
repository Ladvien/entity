from __future__ import annotations

import asyncio

from .core.agent import Agent
from .core.registries import PluginRegistry, SystemRegistries, ToolRegistry
from .core.resources.container import ResourceContainer
from .core.runtime import AgentRuntime
from .infrastructure import DuckDBInfrastructure
from .pipeline.worker import PipelineWorker
from .resources import LLM, Memory, Storage
from .resources.interfaces.duckdb_resource import DuckDBResource
from .resources.interfaces.duckdb_vector_store import DuckDBVectorStore
from .resources.logging import LoggingResource
from .utils.setup_manager import Layer0SetupManager
from .workflows.minimal import minimal_workflow

__all__ = ["Agent", "PipelineWorker", "_create_default_agent"]


def _create_default_agent() -> Agent:
    """Return a minimally configured :class:`Agent`."""
    setup = Layer0SetupManager()
    try:
        asyncio.run(setup.setup())
    except Exception:  # noqa: BLE001 - optional setup
        pass

    agent = Agent()

    db_backend = DuckDBInfrastructure({"path": str(setup.db_path)})
    db_resource = DuckDBResource({})
    db_resource.database = db_backend

    vector_store = DuckDBVectorStore({})
    vector_store.database = db_backend

    memory = Memory({})
    memory.database = db_resource
    memory.vector_store = vector_store

    llm = LLM({})
    storage = Storage({})
    logging_res = LoggingResource({})

    resources = ResourceContainer()

    async def init() -> None:
        await db_backend.initialize()
        await vector_store.initialize()
        await memory.initialize()
        await logging_res.initialize()

        await resources.add("database", db_resource)
        await resources.add("vector_store", vector_store)
        await resources.add("memory", memory)
        await resources.add("llm", llm)
        await resources.add("storage", storage)
        await resources.add("logging", logging_res)

    asyncio.run(init())

    regs = SystemRegistries(
        resources=resources,
        tools=ToolRegistry(),
        plugins=PluginRegistry(),
        validators=None,
    )
    agent._runtime = AgentRuntime(regs, workflow=minimal_workflow)
    return agent
