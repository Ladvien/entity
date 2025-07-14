"""Convenient access to the default Entity agent and helpers."""

from __future__ import annotations

import asyncio
import inspect
import os
from types import SimpleNamespace

from .core.agent import Agent
from .core.plugins import PromptPlugin, ToolPlugin
from .core.registries import SystemRegistries
from .core.resources.container import ResourceContainer
from .core.runtime import AgentRuntime
from .core.stages import PipelineStage
from .infrastructure import DuckDBInfrastructure
from .resources import LLM, Memory, Storage
from .resources.interfaces.duckdb_vector_store import DuckDBVectorStore
from .resources.logging import LoggingResource
from .utils.setup_manager import Layer0SetupManager
from entity.workflows.minimal import minimal_workflow


# ---------------------------------------------------------------------------
# default agent creation
# ---------------------------------------------------------------------------


def _create_default_agent() -> Agent:
    """Return a fully configured default :class:`Agent`."""

    setup = Layer0SetupManager()
    try:  # best effort environment preparation
        asyncio.run(setup.setup())
    except Exception:  # noqa: BLE001
        pass

    agent = Agent()
    builder = agent.builder

    db = DuckDBInfrastructure({"path": str(setup.db_path)})
    llm_provider = None
    try:
        from plugins.builtin.resources.ollama_llm import OllamaLLMResource

        llm_provider = OllamaLLMResource(
            {"model": setup.model, "base_url": setup.base_url}
        )
    except Exception:  # noqa: BLE001 - optional dependency
        pass

    llm = LLM({})
    vector_store = DuckDBVectorStore({})
    memory = Memory({})
    storage = Storage({})
    logging_res = LoggingResource({})

    if llm_provider is not None:
        llm.provider = llm_provider
    memory.database = db
    vector_store.database = db
    memory.vector_store = vector_store

    resources = ResourceContainer()

    async def init_resources() -> None:
        await db.initialize()
        await vector_store.initialize()
        await memory.initialize()
        await logging_res.initialize()

        await resources.add("database", db)
        await resources.add("vector_store", vector_store)
        if llm_provider is not None:
            await resources.add("llm_provider", llm_provider)
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
    global _default_agent
    if _default_agent is None:
        if os.environ.get("ENTITY_AUTO_INIT", "1") != "1":
            raise RuntimeError(
                "ENTITY_AUTO_INIT is disabled; call _create_default_agent() manually"
            )
        _default_agent = _create_default_agent()
    return _default_agent


class _LazyAgent(SimpleNamespace):
    def __getattr__(self, item: str):  # type: ignore[override]
        return getattr(_ensure_agent(), item)

    def __repr__(self) -> str:  # pragma: no cover - convenience
        return repr(_ensure_agent())


agent: Agent | _LazyAgent = _LazyAgent()


# ---------------------------------------------------------------------------
# decorator helpers
# ---------------------------------------------------------------------------

plugin = agent.plugin


def input(func=None, **hints):
    return plugin(func, stage=PipelineStage.INPUT, **hints)


def parse(func=None, **hints):
    return plugin(func, stage=PipelineStage.PARSE, **hints)


def prompt(func=None, **hints):
    return plugin(func, stage=PipelineStage.THINK, **hints)


def tool(func=None, **hints):
    """Register ``func`` as a tool plugin or simple tool."""

    def decorator(f):
        ag = agent
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
