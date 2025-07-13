"""Convenient access to the Entity agent and utilities."""

from __future__ import annotations

from .core.agent import Agent
from .infrastructure import DuckDBInfrastructure
from .resources import LLM, Memory, Storage
from .resources.logging import LoggingResource
from .resources.interfaces.duckdb_vector_store import DuckDBVectorStore
from plugins.builtin.resources.ollama_llm import OllamaLLMResource
from entity.plugins.prompts import BasicErrorHandler
from .core.stages import PipelineStage
from .core.plugins import PromptPlugin, ToolPlugin
from .plugins.prompts.basic_error_handler import BasicErrorHandler
from .utils.setup_manager import Layer0SetupManager
from entity.workflows.default import DefaultWorkflow
from entity.core.registries import SystemRegistries
from entity.core.runtime import AgentRuntime
from entity.core.resources.container import ResourceContainer
import inspect
import asyncio


def _create_default_agent() -> Agent:
    setup = Layer0SetupManager()
    import asyncio

    try:
        asyncio.run(setup.setup())
    except Exception:  # noqa: BLE001 - best effort setup
        pass
    agent = Agent()
    builder = agent.builder

    db = DuckDBInfrastructure({"path": str(setup.db_path)})
    llm_provider = OllamaLLMResource({"model": setup.model, "base_url": setup.base_url})
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
    asyncio.run(builder.add_plugin(BasicErrorHandler({})))
    workflow = getattr(setup, "workflow", DefaultWorkflow())
    agent._runtime = AgentRuntime(caps, workflow=workflow)
    return agent


agent = _create_default_agent()

# Expose decorator helpers bound to the default agent
plugin = agent.plugin


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

    def decorator(f):
        params = list(inspect.signature(f).parameters)
        if params and params[0] in {"ctx", "context"}:
            return agent.plugin(f, stage=PipelineStage.DO, **hints)

        class _WrappedTool(ToolPlugin):
            async def execute_function(self, params_dict):
                return await f(**params_dict)

        asyncio.run(agent.builder.tool_registry.add(f.__name__, _WrappedTool({})))
        return f

    return decorator(func) if func else decorator


agent.tool = tool


def review(func=None, **hints):
    return agent.plugin(func, stage=PipelineStage.REVIEW, **hints)


agent.review = review


def output(func=None, **hints):
    return agent.plugin(func, stage=PipelineStage.OUTPUT, **hints)


agent.output = output


def prompt_plugin(func=None, **hints):
    hints["plugin_class"] = PromptPlugin
    return agent.plugin(func, **hints)


agent.prompt_plugin = prompt_plugin


def tool_plugin(func=None, **hints):
    hints["plugin_class"] = ToolPlugin
    return agent.plugin(func, **hints)


agent.tool_plugin = tool_plugin


__all__ = [
    "core",
    "Agent",
    "agent",
]


def __getattr__(name: str):
    if name == "core":
        from . import core as _core

        return _core
    if name == "AgentBuilder":
        from .core.agent import _AgentBuilder

        return _AgentBuilder
    raise AttributeError(name)
