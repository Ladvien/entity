"""Convenient access to the Entity agent and utilities."""

from __future__ import annotations

from .core.agent import Agent
from .infrastructure import DuckDBInfrastructure
from .resources import LLM, Memory, Storage
from plugins.builtin.resources.ollama_llm import OllamaLLMResource
from .core.stages import PipelineStage
from .core.plugins import PromptPlugin, ToolPlugin
from .utils.setup_manager import Layer0SetupManager
from entity.core.registries import SystemRegistries
from entity.core.runtime import AgentRuntime
from entity.core.resources.container import ResourceContainer


def _create_default_agent() -> Agent:
    setup = Layer0SetupManager()
    try:
        setup.setup_resources()
    except Exception:  # noqa: BLE001 - best effort setup
        pass
    agent = Agent()
    builder = agent.builder

    db = DuckDBInfrastructure({"path": str(setup.db_path)})
    llm_provider = OllamaLLMResource({})
    llm = LLM({})
    memory = Memory({})
    storage = Storage({})

    llm.provider = llm_provider
    memory.database = db

    resources = ResourceContainer()
    import asyncio

    asyncio.run(db.initialize())
    asyncio.run(memory.initialize())
    asyncio.run(resources.add("database", db))
    asyncio.run(resources.add("llm_provider", llm_provider))
    asyncio.run(resources.add("llm", llm))
    asyncio.run(resources.add("memory", memory))
    asyncio.run(resources.add("storage", storage))

    caps = SystemRegistries(
        resources=resources,
        tools=builder.tool_registry,
        plugins=builder.plugin_registry,
    )
    agent._runtime = AgentRuntime(caps)
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
    return agent.plugin(func, stage=PipelineStage.DO, **hints)


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
        from .core.builder import _AgentBuilder

        return _AgentBuilder
    raise AttributeError(name)
