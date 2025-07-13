from __future__ import annotations

"""Pipeline tracing helpers for debugging."""

import time
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Tuple

from entity.pipeline.pipeline import execute_stage, generate_pipeline_id
from entity.pipeline.state import PipelineState, ConversationEntry
from entity.pipeline.stages import PipelineStage
from entity.core.registries import SystemRegistries
from datetime import datetime


@dataclass
class PluginRecord:
    """Information about a plugin executed within a stage."""

    dependencies: List[str]


@dataclass
class StageRecord:
    """Timing and dependency info for a pipeline stage."""

    start: float
    end: float | None = None
    plugins: Dict[str, PluginRecord] = field(default_factory=dict)

    @property
    def duration_ms(self) -> float | None:
        if self.end is None:
            return None
        return (self.end - self.start) * 1000


class StageTracer:
    """Capture timing and dependency data for each pipeline stage."""

    def __init__(self) -> None:
        self.records: Dict[str, StageRecord] = {}

    def start_stage(
        self, stage: PipelineStage, plugins: Dict[str, Iterable[str]]
    ) -> None:
        self.records[stage.name] = StageRecord(time.perf_counter())
        for name, deps in plugins.items():
            self.records[stage.name].plugins[name] = PluginRecord(list(deps))

    def end_stage(self, stage: PipelineStage) -> None:
        record = self.records.get(stage.name)
        if record is not None:
            record.end = time.perf_counter()

    def report(self) -> Dict[str, Dict[str, object]]:
        data: Dict[str, Dict[str, object]] = {}
        for stage, rec in self.records.items():
            plugins = {n: pr.dependencies for n, pr in rec.plugins.items()}
            data[stage] = {"duration_ms": rec.duration_ms, "plugins": plugins}
        return data


class PipelineDebugger:
    """Interactively step through pipeline execution."""

    def __init__(self, registries: SystemRegistries) -> None:
        self.registries = registries
        self.tracer = StageTracer()

    async def run(
        self, message: str, *, user_id: str = "debug"
    ) -> Tuple[dict, StageTracer]:
        state = PipelineState(
            conversation=[
                ConversationEntry(
                    content=message, role="user", timestamp=datetime.now()
                )
            ],
            pipeline_id=f"{user_id}_{generate_pipeline_id()}",
        )
        for stage in [
            PipelineStage.INPUT,
            PipelineStage.PARSE,
            PipelineStage.THINK,
            PipelineStage.DO,
            PipelineStage.REVIEW,
            PipelineStage.OUTPUT,
        ]:
            stage_plugins = self.registries.plugins.get_plugins_for_stage(stage)
            plugin_meta: Dict[str, Iterable[str]] = {}
            for plugin in stage_plugins:
                name = self.registries.plugins.get_plugin_name(plugin)
                deps = getattr(plugin, "dependencies", [])
                plugin_meta[name] = deps
            self.tracer.start_stage(stage, plugin_meta)
            await execute_stage(stage, state, self.registries, user_id=user_id)
            self.tracer.end_stage(stage)
            input(f"Completed {stage.name}. Press Enter to continue...")
            if state.response is not None or state.failure_info is not None:
                break
        return state.response or {}, self.tracer
