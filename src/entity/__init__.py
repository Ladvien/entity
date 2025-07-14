"""Convenient access to the Entity agent and utilities."""

from __future__ import annotations

import asyncio
import inspect


def _handle_import_error(exc: ModuleNotFoundError) -> None:
    """Re-raise missing optional dependency errors with guidance."""

    missing = exc.name
    mapping = {"yaml": "pyyaml", "dotenv": "python-dotenv", "httpx": "httpx"}
    requirement = mapping.get(missing, missing)
    raise ImportError(
        f"Optional dependency '{requirement}' is required. "
        f"Install it with `pip install {requirement}`."
    ) from exc


try:
    from .core.agent import Agent
    from .infrastructure import DuckDBInfrastructure
    from .resources import LLM, Memory, Storage
    from .resources.logging import LoggingResource
    from .resources.interfaces.duckdb_vector_store import DuckDBVectorStore
    from .core.stages import PipelineStage
    from .core.plugins import PromptPlugin, ToolPlugin
    from .utils.setup_manager import Layer0SetupManager
    from entity.workflows.minimal import minimal_workflow
    from entity.core.registries import SystemRegistries
    from entity.core.runtime import AgentRuntime
    from entity.core.resources.container import ResourceContainer
except ModuleNotFoundError as exc:  # pragma: no cover - missing optional deps
    _handle_import_error(exc)


def _create_default_agent() -> Agent:
    setup = Layer0SetupManager()
    import asyncio

    try:
        asyncio.run(setup.setup())
    except Exception:  # noqa: BLE001 - best effort setup
        pass
    agent = Agent()

<<<<<<< HEAD
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
<<<<<<< HEAD
<<<<<<< HEAD
    if llm_provider is not None:
        llm.provider = llm_provider
=======
    llm.provider = None
>>>>>>> pr-1536
=======
    if llm_provider is not None:
        llm.provider = llm_provider
>>>>>>> pr-1539
=======
    llm.provider = None
>>>>>>> pr-1540
    memory.database = db
    memory.vector_store = vector_store
    vector_store.database = db

=======
>>>>>>> pr-1538
    resources = ResourceContainer()
    asyncio.run(resources.add("database", db))
    asyncio.run(resources.add("vector_store", vector_store))
    asyncio.run(resources.add("llm", llm))
    asyncio.run(resources.add("memory", memory))
    asyncio.run(resources.add("storage", storage))
    asyncio.run(resources.add("logging", logging_res))

<<<<<<< HEAD
    async def init() -> None:
        await db_backend.initialize()
        await vector_store.initialize()
        await memory.initialize()
        await logging_res.initialize()

        await resources.add("database", db_resource)
        await resources.add("vector_store", vector_store)
        if llm_provider is not None:
            await resources.add("llm_provider", llm_provider)
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
    try:
        from plugins.builtin.basic_error_handler import BasicErrorHandler
        from plugins.examples import InputLogger

        asyncio.run(builder.add_plugin(BasicErrorHandler({})))
        asyncio.run(builder.add_plugin(InputLogger({})))
    except Exception:  # noqa: BLE001 - optional plugins
        pass

    try:
        from user_plugins.prompts import ComplexPrompt
        from user_plugins.responders import ComplexPromptResponder

        asyncio.run(builder.add_plugin(ComplexPrompt({})))
        asyncio.run(builder.add_plugin(ComplexPromptResponder({})))
    except Exception:  # noqa: BLE001 - optional plugins
        pass
    workflow = getattr(setup, "workflow", minimal_workflow)
    agent._runtime = AgentRuntime(caps, workflow=workflow)
    return agent


agent: Agent | None = None


=======
    agent._runtime = AgentRuntime(
        SystemRegistries(resources=resources), workflow=minimal_workflow
    )
    return agent


>>>>>>> pr-1540
def _ensure_agent() -> Agent:
    global agent
    if agent is None:
        agent = _create_default_agent()
    return agent


# Expose decorator helpers bound to the default agent


def plugin(func=None, **hints):
    ag = _ensure_agent()
    return ag.plugin(func, **hints)


def input(func=None, **hints):
    ag = _ensure_agent()
    return ag.plugin(func, stage=PipelineStage.INPUT, **hints)


def parse(func=None, **hints):
    ag = _ensure_agent()
    return ag.plugin(func, stage=PipelineStage.PARSE, **hints)


def prompt(func=None, **hints):
    ag = _ensure_agent()
    return ag.plugin(func, stage=PipelineStage.THINK, **hints)


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

        ag = _ensure_agent()
        asyncio.run(ag.builder.tool_registry.add(f.__name__, _WrappedTool({})))
        return f

    return decorator(func) if func else decorator


def review(func=None, **hints):
    ag = _ensure_agent()
    return ag.plugin(func, stage=PipelineStage.REVIEW, **hints)


def output(func=None, **hints):
    ag = _ensure_agent()
    return ag.plugin(func, stage=PipelineStage.OUTPUT, **hints)


def prompt_plugin(func=None, **hints):
    hints["plugin_class"] = PromptPlugin
    ag = _ensure_agent()
    return ag.plugin(func, **hints)


def tool_plugin(func=None, **hints):
    hints["plugin_class"] = ToolPlugin
    ag = _ensure_agent()
    return ag.plugin(func, **hints)


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


def __getattr__(name: str):
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
=======
agent = _ensure_agent()
plugin = agent.plugin
>>>>>>> pr-1540
