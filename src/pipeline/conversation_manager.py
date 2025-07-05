from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, cast

from registry import SystemRegistries

from .manager import PipelineManager
from .pipeline import execute_pipeline, generate_pipeline_id
from .state import ConversationEntry, MetricsCollector, PipelineState


class ConversationManager:
    """Coordinate multi-turn processing through repeated pipeline execution."""

    def __init__(
        self,
        registries: SystemRegistries,
        pipeline_manager: PipelineManager | None = None,
        *,
        history_limit: Optional[int] = None,
    ) -> None:
        self._registries = registries
        self._pipeline_manager = pipeline_manager or PipelineManager(registries)
        self._history: List[ConversationEntry] = []
        self._conversation_id = generate_pipeline_id()
        self._history_limit = history_limit

    def _trim_history(self) -> None:
        if self._history_limit is not None and len(self._history) > self._history_limit:
            self._history = self._history[-self._history_limit :]

    async def process_request(self, user_message: str) -> Dict[str, Any]:
        """Process a user message, delegating back to the pipeline when needed."""

        self._history.append(
            ConversationEntry(
                content=user_message, role="user", timestamp=datetime.now()
            )
        )
        self._trim_history()

        state = PipelineState(
            conversation=list(self._history),
            pipeline_id=self._conversation_id,
            metrics=MetricsCollector(),
        )

        response = cast(
            Dict[str, Any],
            await execute_pipeline(
                user_message,
                self._registries,
                pipeline_manager=self._pipeline_manager,
                state=state,
            ),
        )
        self._history = (
            state.conversation[-self._history_limit :]
            if self._history_limit
            else state.conversation
        )
        while (
            isinstance(response, dict) and response.get("type") == "continue_processing"
        ):
            follow_up = str(response.get("message", ""))
            self._history.append(
                ConversationEntry(
                    content=follow_up, role="user", timestamp=datetime.now()
                )
            )
            self._trim_history()
            state = PipelineState(
                conversation=list(self._history),
                pipeline_id=self._conversation_id,
                metrics=MetricsCollector(),
            )
            response = cast(
                Dict[str, Any],
                await execute_pipeline(
                    follow_up,
                    self._registries,
                    pipeline_manager=self._pipeline_manager,
                    state=state,
                ),
            )
            self._history = (
                state.conversation[-self._history_limit :]
                if self._history_limit
                else state.conversation
            )
        return response
