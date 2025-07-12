"""Convenient access to the Entity agent and utilities."""

from __future__ import annotations

from .core.agent import Agent
from .infrastructure import DuckDBInfrastructure
from .resources import LLM, Memory, Storage
from plugins.builtin.resources.ollama_llm import OllamaLLMResource
from plugins.builtin.resources.duckdb_resource import DuckDBResource
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

__all__ = ["core", "Agent", "agent"]


def __getattr__(name: str):
    if name == "core":
        from . import core as _core

        return _core
    if name == "Agent":
        from .core.agent import Agent as _Agent

        return _Agent
    raise AttributeError(name)
