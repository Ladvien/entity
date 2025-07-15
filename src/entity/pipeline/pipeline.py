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
from entity.core.resources.container import ResourceContainer
from entity.core.state import ConversationEntry, FailureInfo
from entity.core.state_logger import StateLogger
from contextlib import asynccontextmanager
from entity.utils.logging import get_logger
from .state import PipelineState

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

STAGE_ORDER = [
    PipelineStage.INPUT,
    PipelineStage.PARSE,
    PipelineStage.THINK,
    PipelineStage.DO,
    PipelineStage.REVIEW,
    PipelineStage.OUTPUT,
]


@asynccontextmanager
async def _noop_async_cm():
    yield


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
            validators=getattr(capabilities, "validators", None),
        )
        return await execute_pipeline(
            message,
            regs,
            user_id=user_id,
            state_logger=state_logger,
            state=state,
            workflow=self.workflow,
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
    stage: PipelineStage,
    state: PipelineState,
    registries: SystemRegistries,
    *,
    user_id: str,
) -> None:
    memory = registries.resources.get("memory") if registries.resources else None
    if memory is not None:
        state.conversation = await memory.load_conversation(
            state.pipeline_id, user_id=user_id
        )
        state.temporary_thoughts = await memory.fetch_persistent(
            f"{state.pipeline_id}_temp",
            {},
            user_id=user_id,
        )
    state.current_stage = stage
    log_res = registries.resources.get("logging") if registries.resources else None
    stage_plugins = registries.plugins.get_plugins_for_stage(stage)
    _start = time.perf_counter()
    if log_res is not None:
        await log_res.log(
            "info",
            "stage started",
            component="pipeline",
            stage=stage,
            pipeline_id=state.pipeline_id,
        )
    async with start_span(f"stage.{stage.name.lower()}"):
        for plugin in stage_plugins:
            context = PluginContext(state, registries, user_id=user_id)
            context.set_current_stage(stage)
            name = registries.plugins.get_plugin_name(plugin)
            context.set_current_plugin(name)
            validators = getattr(registries, "validators", None)
            if validators is not None:
                await validators.validate(stage, context)
            try:
                await plugin.execute(context)
                if stage == PipelineStage.OUTPUT and state.response is not None:
                    break
                if state.pending_tool_calls:
                    tool_results = await execute_pending_tools(
                        state, registries, user_id=user_id
                    )
                    for call in state.pending_tool_calls:
                        result = tool_results.get(call.result_key)
                        context.add_conversation_entry(
                            content=f"Tool result: {result}",
                            role="system",
                            metadata={"tool_name": call.name, "stage": str(stage)},
                        )
                    state.pending_tool_calls.clear()
            except CircuitBreakerTripped as exc:
                if log_res is not None:
                    await log_res.log(
                        "error",
                        "Circuit breaker tripped",
                        component="pipeline",
                        plugin_name=getattr(plugin, "name", plugin.__class__.__name__),
                        stage=stage,
                        pipeline_id=state.pipeline_id,
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
                if log_res is not None:
                    await log_res.log(
                        "error",
                        "Plugin execution failed",
                        component="pipeline",
                        plugin_name=getattr(plugin, "name", plugin.__class__.__name__),
                        stage=stage,
                        pipeline_id=state.pipeline_id,
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
                if log_res is not None:
                    await log_res.log(
                        "error",
                        "Tool execution failed",
                        component="pipeline",
                        plugin_name=exc.tool_name,
                        stage=stage,
                        pipeline_id=state.pipeline_id,
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
                if log_res is not None:
                    await log_res.log(
                        "error",
                        "Resource error",
                        component="pipeline",
                        plugin_name=getattr(plugin, "name", plugin.__class__.__name__),
                        stage=stage,
                        pipeline_id=state.pipeline_id,
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
                if log_res is not None:
                    await log_res.log(
                        "error",
                        "Pipeline error",
                        component="pipeline",
                        plugin_name=getattr(plugin, "name", plugin.__class__.__name__),
                        stage=stage,
                        pipeline_id=state.pipeline_id,
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
                if log_res is not None:
                    await log_res.log(
                        "error",
                        "Unexpected plugin exception",
                        component="pipeline",
                        plugin_name=getattr(plugin, "name", plugin.__class__.__name__),
                        stage=stage,
                        pipeline_id=state.pipeline_id,
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
            await execute_stage(PipelineStage.ERROR, state, registries, user_id=user_id)
            state.last_completed_stage = PipelineStage.ERROR
    if memory is not None:
        await memory.save_conversation(
            state.pipeline_id,
            state.conversation,
            user_id=user_id,
        )
        await memory.store_persistent(
            f"{state.pipeline_id}_temp",
            state.temporary_thoughts,
            user_id=user_id,
        )
    _elapsed = time.perf_counter() - _start
    # elapsed time could be logged here if needed


async def execute_pipeline(
    user_message: str,
    capabilities: SystemRegistries,
    *,
    user_id: str | None = None,
    state_logger: "StateLogger" | None = None,
    state: PipelineState | None = None,
    workflow: Workflow | None = None,
    max_iterations: int = 5,
    checkpoint_key: str | None = None,
) -> Dict[str, Any]:
    if capabilities is None:
        raise TypeError("capabilities is required")
    user_id = user_id or "default"
    resources = capabilities.resources
    manage_container = False
    if isinstance(resources, ResourceContainer):
        if resources.is_active:
            container = resources
        else:
            container = resources.clone()
            manage_container = True
    else:
        container = resources
    memory = container.get("memory") if container else None
    if state is None:
        if checkpoint_key and memory:
            saved = await memory.fetch_persistent(checkpoint_key, None, user_id=user_id)
            if saved:
                state = PipelineState.from_dict(saved)
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

    # Thoughts persist for the duration of a single message run
    # so they can be referenced across iterations. They are cleared
    # only once the message has been fully processed.
    _start = time.time()

    async def _run_pipeline() -> Dict[str, Any]:
        async with start_span("pipeline.execute"):
            while True:
                state.iteration += 1
                start_stage = state.next_stage or STAGE_ORDER[0]
                if state.next_stage is not None:
                    state.next_stage = None
                start_index = STAGE_ORDER.index(start_stage)
                for stage in STAGE_ORDER[start_index:]:
                    if stage in state.skip_stages:
                        state.skip_stages.discard(stage)
                        continue
                    if workflow and not workflow.should_execute(stage, state):
                        continue
                    if (
                        state.last_completed_stage is not None
                        and stage.value <= state.last_completed_stage.value
                    ):
                        continue
                    try:
                        await execute_stage(stage, state, capabilities, user_id=user_id)
                    finally:
                        if state_logger is not None:
                            state_logger.log(state, stage)
                        log_res = container.get("logging") if container else None
                        if log_res is not None:
                            await log_res.log(
                                "info",
                                "stage complete",
                                component="pipeline",
                                stage=stage,
                                pipeline_id=state.pipeline_id,
                                iteration=state.iteration,
                            )
                        if checkpoint_key and memory:
                            await memory.store_persistent(
                                checkpoint_key, state.to_dict(), user_id=user_id
                            )
                    if state.next_stage is not None:
                        state.last_completed_stage = stage
                        break
                    if state.failure_info or state.response is not None:
                        break
                    state.last_completed_stage = stage

                if state.response is not None:
                    break

                if state.next_stage is not None:
                    state.last_completed_stage = None
                    continue

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
                            error_message=(
                                f"No OUTPUT plugin responded after {max_iterations} iterations"
                            ),
                            original_exception=RuntimeError(
                                "max iteration limit reached"
                            ),
                            context_snapshot=state.to_dict(),
                        )
                    break

                state.last_completed_stage = None

        metrics = container.get("metrics_collector") if container else None

        if state.failure_info:
            try:
                if state.last_completed_stage != PipelineStage.ERROR:
                    await execute_stage(
                        PipelineStage.ERROR, state, capabilities, user_id=user_id
                    )
                    if state_logger is not None:
                        state_logger.log(state, PipelineStage.ERROR)
                await execute_stage(
                    PipelineStage.OUTPUT, state, capabilities, user_id=user_id
                )
            except Exception:
                return create_static_error_response(state.pipeline_id).to_dict()
            if state.response is None:
                return create_static_error_response(state.pipeline_id).to_dict()
            result = state.response
        elif state.response is None:
            result = create_default_response("No response generated", state.pipeline_id)
        else:
            result = state.response
        elapsed_ms = (time.time() - _start) * 1000
        if metrics is not None:
            await metrics.record_custom_metric(
                pipeline_id=state.pipeline_id,
                metric_name="pipeline_duration_ms",
                value=elapsed_ms,
            )
        state.stage_results.clear()
        state.temporary_thoughts.clear()
        return result

    if manage_container and hasattr(container, "__aenter__"):
        async with container:
            return await _run_pipeline()
    else:
        return await _run_pipeline()


def visualize_execution_plan(workflow: Workflow, state: PipelineState) -> str:
    """Return a GraphViz dot diagram of the planned execution."""
    lines = ["digraph pipeline {"]
    lines.append("    rankdir=LR")
    prev = "START"
    for stage in STAGE_ORDER:
        if stage in state.skip_stages:
            continue
        if workflow and not workflow.should_execute(stage, state):
            continue
        lines.append(f'    "{prev}" -> "{stage.name}"')
        prev = stage.name
        for plugin in workflow.stage_map.get(stage, []):
            lines.append(f'    "{stage.name}" -> "{plugin}" [style=dotted]')
    lines.append("}")
    return "\n".join(lines)


__all__ = [
    "Workflow",
    "Pipeline",
    "generate_pipeline_id",
    "create_default_response",
    "execute_stage",
    "execute_pipeline",
    "visualize_execution_plan",
]
