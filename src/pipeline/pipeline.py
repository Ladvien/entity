"""Pipeline execution utilities.

This module delegates tool execution to
``pipeline.tools.execution`` to keep logic centralized.
"""

# mypy: ignore-errors

from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict

from entity.core.context import PluginContext
from entity.core.registries import PluginRegistry, SystemRegistries
from entity.core.state import ConversationEntry, FailureInfo
from entity.core.state_logger import StateLogger
from entity.utils.logging import get_logger
from pipeline.state import PipelineState

from .errors import create_static_error_response
from .exceptions import MaxIterationsExceeded  # noqa: F401 - reserved for future use
from .exceptions import (
    CircuitBreakerTripped,
    PipelineError,
    PluginExecutionError,
    ResourceError,
    ToolExecutionError,
)
from .observability.tracing import start_span
from .stages import PipelineStage
from .tools.execution import execute_pending_tools
from .workflow import Workflow

logger = get_logger(__name__)


class Pipeline:
    """Execute messages according to a workflow."""

    def __init__(self, approach: Workflow | Dict[Any, Any]) -> None:
        self.workflow = (
            approach if isinstance(approach, Workflow) else Workflow.from_dict(approach)
        )

    async def run_message(
        self,
        message: str,
        capabilities: SystemRegistries,
        *,
        user_id: str | None = None,
        state_logger: StateLogger | None = None,
        state: PipelineState | None = None,
        max_iterations: int = 5,
    ) -> Dict[str, Any]:
        plugin_reg = PluginRegistry()
        for stage, plugin_names in self.workflow.stage_map.items():
            for name in plugin_names:
                plugin = capabilities.plugins.get_by_name(name)
                if plugin is None:
                    raise KeyError(f"Plugin '{name}' not registered")
                await plugin_reg.register_plugin_for_stage(plugin, stage, name)

        regs = SystemRegistries(
            resources=capabilities.resources,
            tools=capabilities.tools,
            plugins=plugin_reg,
            validators=capabilities.validators,
        )
        return await execute_pipeline(
            message,
            regs,
            user_id=user_id,
            state_logger=state_logger,
            state=state,
            max_iterations=max_iterations,
        )


def generate_pipeline_id() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S%f")


def create_default_response(message: str, pipeline_id: str) -> Dict[str, Any]:
    return {
        "message": message,
        "pipeline_id": pipeline_id,
        "timestamp": datetime.now().isoformat(),
        "type": "default_response",
    }


async def execute_stage(
    stage: PipelineStage, state: PipelineState, registries: SystemRegistries
) -> None:
    state.current_stage = stage
    stage_plugins = registries.plugins.get_plugins_for_stage(stage)
    start = time.perf_counter()
    async with start_span(f"stage.{stage.name.lower()}"):
        for plugin in stage_plugins:
            context = PluginContext(state, registries, user_id)
            context.set_current_stage(stage)
            name = registries.plugins.get_plugin_name(plugin)
            context.set_current_plugin(name)
            if registries.validators is not None:
                await registries.validators.validate(stage, context)
            try:
                await plugin.execute(context)
                if stage == PipelineStage.OUTPUT and state.response is not None:
                    break
                if state.pending_tool_calls:
                    tool_results = await execute_pending_tools(state, registries)
                    for call in state.pending_tool_calls:
                        result = tool_results.get(call.result_key)
                        context.add_conversation_entry(
                            content=f"Tool result: {result}",
                            role="system",
                            metadata={"tool_name": call.name, "stage": str(stage)},
                        )
                    state.pending_tool_calls.clear()
            except CircuitBreakerTripped as exc:
                logger.exception(
                    "Circuit breaker tripped",
                    extra={
                        "plugin": getattr(plugin, "name", plugin.__class__.__name__),
                        "stage": str(stage),
                        "pipeline_id": state.pipeline_id,
                    },
                )
                state.failure_info = FailureInfo(
                    stage=str(stage),
                    plugin_name=getattr(plugin, "name", plugin.__class__.__name__),
                    error_type="circuit_breaker",
                    error_message=str(exc),
                    original_exception=exc,
                    context_snapshot=state.to_dict(),
                )
            except PluginExecutionError as exc:
                logger.exception(
                    "Plugin execution failed",
                    extra={
                        "plugin": getattr(plugin, "name", plugin.__class__.__name__),
                        "stage": str(stage),
                        "pipeline_id": state.pipeline_id,
                    },
                )
                state.failure_info = FailureInfo(
                    stage=str(stage),
                    plugin_name=getattr(plugin, "name", plugin.__class__.__name__),
                    error_type=exc.original_exception.__class__.__name__,
                    error_message=str(exc.original_exception),
                    original_exception=exc.original_exception,
                    context_snapshot=state.to_dict(),
                )
            except ToolExecutionError as exc:
                logger.exception(
                    "Tool execution failed",
                    extra={
                        "plugin": exc.tool_name,
                        "stage": str(stage),
                        "pipeline_id": state.pipeline_id,
                    },
                )
                state.failure_info = FailureInfo(
                    stage=str(stage),
                    plugin_name=exc.tool_name,
                    error_type=exc.original_exception.__class__.__name__,
                    error_message=str(exc.original_exception),
                    original_exception=exc.original_exception,
                    context_snapshot=state.to_dict(),
                )
            except ResourceError as exc:
                logger.exception(
                    "Resource error",
                    extra={
                        "plugin": getattr(plugin, "name", plugin.__class__.__name__),
                        "stage": str(stage),
                        "pipeline_id": state.pipeline_id,
                    },
                )
                state.failure_info = FailureInfo(
                    stage=str(stage),
                    plugin_name=getattr(plugin, "name", plugin.__class__.__name__),
                    error_type=exc.__class__.__name__,
                    error_message=str(exc),
                    original_exception=exc,
                    context_snapshot=state.to_dict(),
                )
            except PipelineError as exc:
                logger.exception(
                    "Pipeline error",
                    extra={
                        "plugin": getattr(plugin, "name", plugin.__class__.__name__),
                        "stage": str(stage),
                        "pipeline_id": state.pipeline_id,
                    },
                )
                state.failure_info = FailureInfo(
                    stage=str(stage),
                    plugin_name=getattr(plugin, "name", plugin.__class__.__name__),
                    error_type=exc.__class__.__name__,
                    error_message=str(exc),
                    original_exception=exc,
                    context_snapshot=state.to_dict(),
                )
            except Exception as exc:  # noqa: BLE001
                logger.exception(
                    "Unexpected plugin exception",
                    exc_info=exc,
                    extra={
                        "plugin": getattr(plugin, "name", plugin.__class__.__name__),
                        "stage": str(stage),
                        "pipeline_id": state.pipeline_id,
                    },
                )

                message = exc.args[0] if exc.args else str(exc)
                state.failure_info = FailureInfo(
                    stage=str(stage),
                    plugin_name=getattr(plugin, "name", plugin.__class__.__name__),
                    error_type=exc.__class__.__name__,
                    error_message=message,
                    original_exception=exc,
                    context_snapshot=state.to_dict(),
                )
            if state.failure_info:
                break
        if state.failure_info and stage != PipelineStage.ERROR:
            await execute_stage(PipelineStage.ERROR, state, registries)
            state.last_completed_stage = PipelineStage.ERROR
    duration = time.perf_counter() - start


async def execute_pipeline(
    user_message: str,
    capabilities: SystemRegistries,
    *,
    user_id: str | None = None,
    state_logger: "StateLogger" | None = None,
    state: PipelineState | None = None,
    max_iterations: int = 5,
) -> Dict[str, Any]:
    if capabilities is None:
        raise TypeError("capabilities is required")
    user_id = user_id or "default"
    if state is None:
        state = PipelineState(
            conversation=[
                ConversationEntry(
                    content=user_message,
                    role="user",
                    timestamp=datetime.now(),
                )
            ],
            pipeline_id=f"{user_id}_{generate_pipeline_id()}",
        )
        state.stage_results.clear()
    start = time.time()
    async with capabilities.resources:
        async with start_span("pipeline.execute"):
            while True:
                state.iteration += 1
                for stage in [
                    PipelineStage.INPUT,
                    PipelineStage.PARSE,
                    PipelineStage.THINK,
                    PipelineStage.DO,
                    PipelineStage.REVIEW,
                    PipelineStage.OUTPUT,
                ]:
                    if (
                        state.last_completed_stage is not None
                        and stage.value <= state.last_completed_stage.value
                    ):
                        continue
                    try:
                        await execute_stage(stage, state, capabilities)
                    finally:
                        if state_logger is not None:
                            state_logger.log(state, stage)
                        logger.info(
                            "stage complete",
                            extra={
                                "stage": str(stage),
                                "pipeline_id": state.pipeline_id,
                                "iteration": state.iteration,
                            },
                        )
                    if state.failure_info:
                        break
                    state.last_completed_stage = stage

                if (
                    state.response is not None
                    and state.last_completed_stage == PipelineStage.OUTPUT
                ):
                    break

                if state.failure_info is not None or state.iteration >= max_iterations:
                    if (
                        state.response is None
                        and state.failure_info is None
                        and state.iteration >= max_iterations
                    ):
                        state.failure_info = FailureInfo(
                            stage="iteration_guard",
                            plugin_name="pipeline",
                            error_type="max_iterations",
                            error_message=f"Reached {max_iterations} iterations",
                            original_exception=RuntimeError(
                                "max iteration limit reached"
                            ),
                            context_snapshot=state.to_dict(),
                        )
                    break

                state.last_completed_stage = None

        if state.failure_info:
            try:
                if state.last_completed_stage != PipelineStage.ERROR:
                    await execute_stage(PipelineStage.ERROR, state, capabilities)
                    if state_logger is not None:
                        state_logger.log(state, PipelineStage.ERROR)
                await execute_stage(PipelineStage.OUTPUT, state, capabilities)
            except Exception:
                result = create_static_error_response(state.pipeline_id).to_dict()
                return result
            if state.response is None:
                result = create_static_error_response(state.pipeline_id).to_dict()
            else:
                result = state.response
        elif state.response is None:
            result = create_default_response("No response generated", state.pipeline_id)
        else:
            result = state.response
        return result


__all__ = [
    "Workflow",
    "Pipeline",
    "generate_pipeline_id",
    "create_default_response",
    "execute_stage",
    "execute_pipeline",
]
