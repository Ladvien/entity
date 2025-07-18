"""Utility helpers for tests."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Mapping
from typing import Any

from entity.core.context import PluginContext
from entity.core.registries import PluginRegistry, SystemRegistries, ToolRegistry
from entity.core.resources.container import ResourceContainer
from entity.core.state import PipelineState
from entity.pipeline.stages import PipelineStage


async def make_async_context(
    stage: PipelineStage = PipelineStage.THINK,
    state: PipelineState | None = None,
    *,
    memory: Any | None = None,
    storage: Any | None = None,
    llm: Any | None = None,
    tools: Mapping[str, Callable] | None = None,
) -> PluginContext:
    """Return a ready-to-use :class:`PluginContext`."""
    if state is None:
        state = PipelineState(conversation=[])

    resources = ResourceContainer()
    if memory is not None:
        await resources.add("memory", memory)
    if storage is not None:
        await resources.add("storage", storage)
    if llm is not None:
        await resources.add("llm", llm)

    tool_registry = ToolRegistry()
    if tools:
        for name, func in tools.items():
            await tool_registry.add(name, func)

    registries = SystemRegistries(
        resources=resources,
        tools=tool_registry,
        plugins=PluginRegistry(),
    )

    ctx = PluginContext(state, registries)
    ctx.set_current_stage(stage)
    ctx.set_current_plugin("test")
    return ctx


def make_context(
    stage: PipelineStage = PipelineStage.THINK,
    state: PipelineState | None = None,
    **kwargs: Any,
) -> PluginContext:
    """Synchronous wrapper for :func:`make_async_context`."""
    return asyncio.run(make_async_context(stage, state, **kwargs))
