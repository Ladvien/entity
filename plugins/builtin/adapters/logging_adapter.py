from __future__ import annotations

from pipeline.base_plugins import AdapterPlugin
from pipeline.context import PluginContext
from pipeline.stages import PipelineStage


class LoggingAdapter(AdapterPlugin):
    """Log the final pipeline response."""

    stages = [PipelineStage.DELIVER]

    async def _execute_impl(self, context: PluginContext) -> None:
        try:
            state = object.__getattribute__(context, "_PluginContext__state")
            response = state.response
        except Exception:  # pragma: no cover - defensive
            response = None
        self.logger.info(
            "Pipeline response",
            extra={
                "pipeline_id": context.pipeline_id,
                "request_id": context.request_id,
                "stage": str(context.current_stage),
                "response": response,
            },
        )
