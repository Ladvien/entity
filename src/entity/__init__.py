from __future__ import annotations

import asyncio
<<<<<<< HEAD
<<<<<<< HEAD
import inspect
import os
from types import SimpleNamespace
=======
>>>>>>> pr-1536

from .core.agent import Agent
from .core.registries import SystemRegistries
=======

from .core.agent import Agent
from .core.registries import PluginRegistry, SystemRegistries, ToolRegistry
>>>>>>> pr-1538
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

<<<<<<< HEAD
<<<<<<< HEAD

# ---------------------------------------------------------------------------
# default agent creation
# ---------------------------------------------------------------------------
=======
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
>>>>>>> pr-1536


def _create_default_agent() -> Agent:
    """Return a minimally configured default agent."""

    setup = Layer0SetupManager()
    try:
        asyncio.run(setup.setup())
    except Exception:
=======
__all__ = ["Agent", "PipelineWorker", "_create_default_agent"]


def _create_default_agent() -> Agent:
    """Return a minimally configured :class:`Agent`."""
    setup = Layer0SetupManager()
    try:
        asyncio.run(setup.setup())
    except Exception:  # noqa: BLE001 - optional setup
>>>>>>> pr-1538
        pass

    agent = Agent()

<<<<<<< HEAD
    db = DuckDBInfrastructure({"path": str(setup.db_path)})
<<<<<<< HEAD
    llm_provider = None
    try:
        from plugins.builtin.resources.ollama_llm import OllamaLLMResource

        llm_provider = OllamaLLMResource(
            {"model": setup.model, "base_url": setup.base_url}
        )
    except Exception:  # noqa: BLE001 - optional dependency
        pass

    llm = LLM({})
=======
>>>>>>> pr-1536
=======
    db_backend = DuckDBInfrastructure({"path": str(setup.db_path)})
    db_resource = DuckDBResource({})
    db_resource.database = db_backend

>>>>>>> pr-1538
    vector_store = DuckDBVectorStore({})
    vector_store.database = db_backend

    memory = Memory({})
<<<<<<< HEAD
=======
    memory.database = db_resource
    memory.vector_store = vector_store

>>>>>>> pr-1538
    llm = LLM({})
    storage = Storage({})
    logging_res = LoggingResource({})

<<<<<<< HEAD
<<<<<<< HEAD
    if llm_provider is not None:
        llm.provider = llm_provider
=======
    llm.provider = None
>>>>>>> pr-1536
    memory.database = db
    memory.vector_store = vector_store
    vector_store.database = db

=======
>>>>>>> pr-1538
    resources = ResourceContainer()

    async def init() -> None:
        await db_backend.initialize()
        await vector_store.initialize()
        await memory.initialize()
        await logging_res.initialize()

        await resources.add("database", db_resource)
        await resources.add("vector_store", vector_store)
<<<<<<< HEAD
<<<<<<< HEAD
        if llm_provider is not None:
            await resources.add("llm_provider", llm_provider)
=======
>>>>>>> pr-1536
        await resources.add("llm", llm)
=======
>>>>>>> pr-1538
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
<<<<<<< HEAD
<<<<<<< HEAD

    try:  # optional default plugins
        from plugins.builtin.basic_error_handler import BasicErrorHandler
        from plugins.examples import InputLogger, MessageParser, ResponseReviewer
        from user_plugins.prompts import ComplexPrompt
        from user_plugins.responders import ComplexPromptResponder

        asyncio.run(builder.add_plugin(BasicErrorHandler({})))
        asyncio.run(builder.add_plugin(InputLogger({})))
        asyncio.run(builder.add_plugin(MessageParser({})))
        asyncio.run(builder.add_plugin(ResponseReviewer({})))
        asyncio.run(builder.add_plugin(ComplexPrompt({})))
        asyncio.run(builder.add_plugin(ComplexPromptResponder({})))
    except Exception:  # noqa: BLE001
        pass

    wf = getattr(setup, "workflow", None)
    workflow = wf if wf is not None else minimal_workflow
    agent._runtime = AgentRuntime(caps, workflow=workflow)
    return agent


# ---------------------------------------------------------------------------
# lazy global agent setup
# ---------------------------------------------------------------------------

_default_agent: Agent | None = None


def _ensure_agent() -> Agent:
    """Return the default agent, creating it if needed."""

    global _default_agent
    if _default_agent is None:
        if os.environ.get("ENTITY_AUTO_INIT", "1") != "1":
            raise RuntimeError(
                "ENTITY_AUTO_INIT is disabled; call _create_default_agent() manually"
            )
        _default_agent = _create_default_agent()
    return _default_agent


class _LazyAgent(SimpleNamespace):
    def __getattr__(self, item):  # type: ignore[override]
        return getattr(_ensure_agent(), item)

    def __repr__(self) -> str:  # pragma: no cover - convenience
        return repr(_ensure_agent())


agent: Agent | _LazyAgent = _LazyAgent()


# ---------------------------------------------------------------------------
# decorator helpers
# ---------------------------------------------------------------------------


def plugin(func=None, **hints):
    ag = _ensure_agent()
    return ag.plugin(func, **hints)


def input(func=None, **hints):
    return plugin(func, stage=PipelineStage.INPUT, **hints)


def parse(func=None, **hints):
    return plugin(func, stage=PipelineStage.PARSE, **hints)


def prompt(func=None, **hints):
    return plugin(func, stage=PipelineStage.THINK, **hints)


def tool(func=None, **hints):
    """Register ``func`` as a tool plugin or simple tool."""

    def decorator(f):
        ag = _ensure_agent()
        params = list(inspect.signature(f).parameters)
        if params and params[0] in {"ctx", "context"}:
            return ag.plugin(f, stage=PipelineStage.DO, **hints)

        class _WrappedTool(ToolPlugin):
            async def execute_function(self, params_dict):
                return await f(**params_dict)

        asyncio.run(ag.builder.tool_registry.add(f.__name__, _WrappedTool({})))
        return f

    return decorator(func) if func else decorator


def review(func=None, **hints):
    return plugin(func, stage=PipelineStage.REVIEW, **hints)


def output(func=None, **hints):
    return plugin(func, stage=PipelineStage.OUTPUT, **hints)


def prompt_plugin(func=None, **hints):
    hints["plugin_class"] = PromptPlugin
    return plugin(func, **hints)


def tool_plugin(func=None, **hints):
    hints["plugin_class"] = ToolPlugin
    return plugin(func, **hints)


__all__ = [
    "core",
    "Agent",
    "agent",
    "_create_default_agent",
    "plugin",
    "input",
    "parse",
    "prompt",
    "tool",
    "review",
    "output",
    "prompt_plugin",
    "tool_plugin",
]


def __getattr__(name: str):  # pragma: no cover - lazily loaded modules
    if name == "core":
        from . import core as _core

        return _core
    if name == "AgentBuilder":
        from .core.agent import _AgentBuilder

        return _AgentBuilder
    raise AttributeError(name)
=======
    agent._runtime = AgentRuntime(caps, workflow=minimal_workflow)
    return agent
>>>>>>> pr-1536
=======
    agent._runtime = AgentRuntime(regs, workflow=minimal_workflow)
    return agent
>>>>>>> pr-1538
