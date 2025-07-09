"""Pipeline execution utilities.

This module delegates tool execution to
``pipeline.tools.execution`` to keep logic centralized.
"""

from __future__ import annotations

import time
import warnings
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict

from entity.core.registries import PluginRegistry, SystemRegistries
from entity.core.state import MetricsCollector
from entity.core.state_logger import StateLogger

from entity.core.context import PluginContext
from entity.core.state import ConversationEntry
from .errors import create_static_error_response
from .exceptions import MaxIterationsExceeded  # noqa: F401 - reserved for future use
from .exceptions import (
    CircuitBreakerTripped,
    PipelineError,
    PluginExecutionError,
    ResourceError,
    ToolExecutionError,
)
from entity.utils.logging import get_logger
from .manager import PipelineManager
from .observability.metrics import MetricsServerManager
from .observability.tracing import start_span
from .stages import PipelineStage
from entity.core.state import FailureInfo, PipelineState
from .tools.execution import execute_pending_tools

logger = get_logger(__name__)


@dataclass
class Workflow:
    """Simple stage to plugin name mapping."""

    stage_map: dict[PipelineStage, list[str]]

    @classmethod
    def from_dict(cls, data: Dict[Any, Any]) -> "Workflow":
        mapping: dict[PipelineStage, list[str]] = {}
        for stage, plugins in data.items():
            stage_enum = PipelineStage.ensure(stage)
            names = plugins if isinstance(plugins, list) else [plugins]
            mapping[stage_enum] = [str(p) for p in names]
        return cls(mapping)


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
        state_logger: StateLogger | None = None,
        return_metrics: bool = False,
        state: PipelineState | None = None,
        max_iterations: int = 5,
    ) -> Dict[str, Any] | tuple[Dict[str, Any], MetricsCollector]:
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
            state_logger=state_logger,
            return_metrics=return_metrics,
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
            context = PluginContext(state, registries)
            context.set_current_stage(stage)
            await registries.validators.validate(stage, context)
            plugin_name = registries.plugins.get_plugin_name(plugin)
            start_plugin = time.perf_counter()
            try:
                await plugin.execute(context)
                plugin_duration = time.perf_counter() - start_plugin
                if state.metrics:
                    key = f"{stage}:{plugin_name}"
                    state.metrics.record_plugin_duration(key, plugin_duration)
                if stage == PipelineStage.DELIVER and state.response is not None:
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
                )
            if state.failure_info:
                break
        if state.failure_info and stage != PipelineStage.ERROR:
            await execute_stage(PipelineStage.ERROR, state, registries)
            state.last_completed_stage = PipelineStage.ERROR
    duration = time.perf_counter() - start
    if state.metrics:
        state.metrics.record_stage_duration(str(stage), duration)


async def execute_pipeline(
    user_message: str,
    capabilities: SystemRegistries,
    *,
    state_logger: "StateLogger" | None = None,
    return_metrics: bool = False,
    state: PipelineState | None = None,
    max_iterations: int = 5,
) -> Dict[str, Any] | tuple[Dict[str, Any], MetricsCollector]:
    if capabilities is None and registries is not None:
        warnings.warn(
            "'registries' is deprecated, use 'capabilities' instead",
            DeprecationWarning,
            stacklevel=2,
        )
        capabilities = registries
    if capabilities is None:
        raise TypeError("capabilities is required")
    if state is None:
        state = PipelineState(
            conversation=[
                ConversationEntry(
                    content=user_message, role="user", timestamp=datetime.now()
                )
            ],
            pipeline_id=generate_pipeline_id(),
            metrics=MetricsCollector(),
        )
    start = time.time()
    try:
        async with capabilities.resources:
            async with start_span("pipeline.execute"):
                while True:
                    state.iteration += 1
                    for stage in [
                        PipelineStage.PARSE,
                        PipelineStage.THINK,
                        PipelineStage.DO,
                        PipelineStage.REVIEW,
                        PipelineStage.DELIVER,
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
                        and state.last_completed_stage == PipelineStage.DELIVER
                    ):
                        break

                    if (
                        state.failure_info is not None
                        or state.iteration >= max_iterations
                    ):
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
                            )
                        break

                    state.last_completed_stage = None

        if state.failure_info:
            try:
                if state.last_completed_stage != PipelineStage.ERROR:
                    await execute_stage(PipelineStage.ERROR, state, capabilities)
                    if state_logger is not None:
                        state_logger.log(state, PipelineStage.ERROR)
                await execute_stage(PipelineStage.DELIVER, state, capabilities)
            except Exception:
                result = create_static_error_response(state.pipeline_id).to_dict()
                return (result, state.metrics) if return_metrics else result
            if state.response is None:
                result = create_static_error_response(state.pipeline_id).to_dict()
            else:
                result = state.response
        elif state.response is None:
            result = create_default_response("No response generated", state.pipeline_id)
        else:
            result = state.response
        return (result, state.metrics) if return_metrics else result
    finally:
        if state.metrics:
            state.metrics.record_pipeline_duration(time.time() - start)
        server = MetricsServerManager.get()
        if server is not None and state.metrics:
            server.update(state.metrics)


__all__ = [
    "Workflow",
    "Pipeline",
    "generate_pipeline_id",
    "create_default_response",
    "execute_stage",
    "execute_pipeline",
]
