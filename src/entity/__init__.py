"""Convenient access to the Entity agent and helpers."""

from __future__ import annotations

import asyncio
import inspect
<<<<<<< HEAD


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
<<<<<<< HEAD
=======
    from plugins.builtin.resources.ollama_llm import OllamaLLMResource
    from plugins.builtin.basic_error_handler import BasicErrorHandler
    from plugins.examples import InputLogger, MessageParser, ResponseReviewer
>>>>>>> pr-1529
    from .core.stages import PipelineStage
    from .core.plugins import PromptPlugin, ToolPlugin
    from .utils.setup_manager import Layer0SetupManager
    from entity.workflows.minimal import minimal_workflow
    from entity.core.registries import SystemRegistries
    from entity.core.runtime import AgentRuntime
    from entity.core.resources.container import ResourceContainer
except ModuleNotFoundError as exc:  # pragma: no cover - missing optional deps
    _handle_import_error(exc)
=======
import os
from types import SimpleNamespace

from .core.agent import Agent
from .core.plugins import PromptPlugin, ToolPlugin
from .core.resources.container import ResourceContainer
from .core.registries import SystemRegistries
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
>>>>>>> pr-1530


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
<<<<<<< HEAD
    llm_provider = OllamaLLMResource({"model": setup.model, "base_url": setup.base_url})
=======
    llm_provider = None
    try:
        from plugins.builtin.resources.ollama_llm import OllamaLLMResource

        llm_provider = OllamaLLMResource(
            {"model": setup.model, "base_url": setup.base_url}
        )
    except Exception:  # noqa: BLE001 - optional dependency
        pass

>>>>>>> pr-1530
    llm = LLM({})
    vector_store = DuckDBVectorStore({})
    memory = Memory({})
    storage = Storage({})
    logging_res = LoggingResource({})

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
<<<<<<< HEAD
<<<<<<< HEAD
    # Default plugins are optional and may not be available in all environments
    try:
=======

    try:  # optional default plugins
>>>>>>> pr-1530
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
<<<<<<< HEAD
    except Exception:  # noqa: BLE001 - plugins optional
=======
    asyncio.run(builder.add_plugin(BasicErrorHandler({})))
    asyncio.run(builder.add_plugin(InputLogger({})))
    try:
        from user_plugins.prompts import ComplexPrompt
        from user_plugins.responders import ComplexPromptResponder

        asyncio.run(builder.add_plugin(ComplexPrompt({})))
        asyncio.run(builder.add_plugin(ComplexPromptResponder({})))
    except Exception:  # noqa: BLE001 - optional plugins
>>>>>>> pr-1529
        pass
    workflow = getattr(setup, "workflow", minimal_workflow)
=======
    except Exception:  # noqa: BLE001
        pass

    wf = getattr(setup, "workflow", None)
    workflow = wf if wf is not None else minimal_workflow
>>>>>>> pr-1530
    agent._runtime = AgentRuntime(caps, workflow=workflow)
    return agent


<<<<<<< HEAD
<<<<<<< HEAD
try:
    agent = _create_default_agent()
except Exception:  # noqa: BLE001 - optional defaults
    agent = Agent()
=======
agent: Agent | None = None
=======
# ---------------------------------------------------------------------------
# lazy global agent setup
# ---------------------------------------------------------------------------

_default_agent: Agent | None = None
>>>>>>> pr-1530


def _ensure_agent() -> Agent:
    global _default_agent
    if _default_agent is None:
        _default_agent = _create_default_agent()
    return _default_agent

<<<<<<< HEAD
>>>>>>> pr-1529

# Expose decorator helpers bound to the default agent
plugin = agent.plugin


<<<<<<< HEAD
def input(func=None, **hints):
    return agent.plugin(func, stage=PipelineStage.INPUT, **hints)


agent.input = input


def parse(func=None, **hints):
    return agent.plugin(func, stage=PipelineStage.PARSE, **hints)


agent.parse = parse


def prompt(func=None, **hints):
    return agent.plugin(func, stage=PipelineStage.THINK, **hints)


agent.prompt = prompt


def tool(func=None, **hints):
    """Register ``func`` as a tool plugin or simple tool."""

=======
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
=======

class _LazyAgent(SimpleNamespace):
    def __getattr__(self, item):  # type: ignore[override]
        return getattr(_ensure_agent(), item)

    def __repr__(self) -> str:  # pragma: no cover - convenience
        return repr(_ensure_agent())


if os.environ.get("ENTITY_AUTO_INIT", "1") == "1":
    _default_agent = _create_default_agent()

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
>>>>>>> pr-1530


def tool(func=None, **hints):
    """Register ``func`` as a tool plugin or simple tool."""

<<<<<<< HEAD
>>>>>>> pr-1529
=======
>>>>>>> pr-1530
    def decorator(f):
        params = list(inspect.signature(f).parameters)
        if params and params[0] in {"ctx", "context"}:
<<<<<<< HEAD
<<<<<<< HEAD
            return agent.plugin(f, stage=PipelineStage.DO, **hints)
=======
            return ag.plugin(f, stage=PipelineStage.DO, **hints)
>>>>>>> pr-1529
=======
            return ag.plugin(f, stage=PipelineStage.DO, **hints)
>>>>>>> pr-1530

        class _WrappedTool(ToolPlugin):
            async def execute_function(self, params_dict):
                return await f(**params_dict)

<<<<<<< HEAD
<<<<<<< HEAD
        asyncio.run(agent.builder.tool_registry.add(f.__name__, _WrappedTool({})))
        return f

    return decorator(func) if func else decorator


agent.tool = tool
=======
        ag = _ensure_agent()
=======
>>>>>>> pr-1530
        asyncio.run(ag.builder.tool_registry.add(f.__name__, _WrappedTool({})))
        return f

    return decorator(func) if func else decorator
<<<<<<< HEAD
>>>>>>> pr-1529


def review(func=None, **hints):
    return agent.plugin(func, stage=PipelineStage.REVIEW, **hints)


agent.review = review


def output(func=None, **hints):
    return agent.plugin(func, stage=PipelineStage.OUTPUT, **hints)


agent.output = output
=======


def review(func=None, **hints):
    return plugin(func, stage=PipelineStage.REVIEW, **hints)


def output(func=None, **hints):
    return plugin(func, stage=PipelineStage.OUTPUT, **hints)
>>>>>>> pr-1530


def prompt_plugin(func=None, **hints):
    hints["plugin_class"] = PromptPlugin
<<<<<<< HEAD
    return agent.plugin(func, **hints)


agent.prompt_plugin = prompt_plugin
=======
    return plugin(func, **hints)
>>>>>>> pr-1530


def tool_plugin(func=None, **hints):
    hints["plugin_class"] = ToolPlugin
<<<<<<< HEAD
<<<<<<< HEAD
    return agent.plugin(func, **hints)


agent.tool_plugin = tool_plugin
=======
    ag = _ensure_agent()
    return ag.plugin(func, **hints)
>>>>>>> pr-1529
=======
    return plugin(func, **hints)
>>>>>>> pr-1530


__all__ = [
    "core",
    "Agent",
    "agent",
<<<<<<< HEAD
<<<<<<< HEAD
=======
=======
>>>>>>> pr-1530
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
<<<<<<< HEAD
>>>>>>> pr-1529
=======
>>>>>>> pr-1530
]


def __getattr__(name: str):  # pragma: no cover - lazily loaded modules
    if name == "core":
        from . import core as _core

        return _core
    raise AttributeError(name)
