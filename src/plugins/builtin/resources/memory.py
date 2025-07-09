from __future__ import annotations

"""Unified memory resource with optional persistence and search."""

from typing import Any, Dict, List, Optional, TYPE_CHECKING, cast

from datetime import datetime

from pipeline.base_plugins import ResourcePlugin, ValidationResult
from pipeline.manager import PipelineManager
from pipeline.pipeline import execute_pipeline, generate_pipeline_id
from pipeline.state import ConversationEntry, MetricsCollector, PipelineState
from pipeline.stages import PipelineStage
from plugins.builtin.resources.vector_store import VectorStoreResource
from registry import SystemRegistries

from .database import DatabaseResource

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    pass


class Memory(ResourcePlugin):
    """Store key/value data and conversation history."""

    stages = [PipelineStage.PARSE]
    name = "memory"
    dependencies = ["database", "vector_store"]

    def __init__(
        self,
        database: DatabaseResource | None = None,
        vector_store: VectorStoreResource | None = None,
        config: Dict | None = None,
    ) -> None:
        super().__init__(config or {})
        self.database = database
        self.vector_store = vector_store
        self._kv: Dict[str, Any] = {}
        self._conversations: Dict[str, List[ConversationEntry]] = {}
        self._conversation_manager: Memory.ConversationSession | None = None

    @classmethod
    def from_config(cls, config: Dict) -> "Memory":
        return cls(None, None, config=config)

    async def _execute_impl(self, context) -> None:  # pragma: no cover - no op
        return None

    def get(self, key: str, default: Any | None = None) -> Any:
        return self._kv.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._kv[key] = value

    def clear(self) -> None:
        self._kv.clear()

    async def save_conversation(
        self, conversation_id: str, history: List[ConversationEntry]
    ) -> None:
        if self.database:
            await self.database.save_history(conversation_id, history)
        else:
            self._conversations[conversation_id] = list(history)

    async def load_conversation(self, conversation_id: str) -> List[ConversationEntry]:
        if self.database:
            return await self.database.load_history(conversation_id)
        return list(self._conversations.get(conversation_id, []))

    async def search_similar(self, query: str, k: int = 5) -> List[str]:
        if self.vector_store:
            return await self.vector_store.query_similar(query, k)
        return []

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        for name in ("database", "vector_store"):
            sub = config.get(name)
            if sub is not None and not isinstance(sub, dict):
                return ValidationResult.error_result(f"'{name}' must be a mapping")
        return ValidationResult.success_result()

    class ConversationSession:
        """Handle multi-turn conversations using the parent memory."""

        def __init__(
            self,
            memory: "Memory",
            registries: SystemRegistries,
            pipeline_manager: PipelineManager | None = None,
            *,
            history_limit: int | None = None,
        ) -> None:
            self._memory = memory
            self._registries = registries
            self._pipeline_manager = pipeline_manager or PipelineManager(registries)
            self._history_limit = history_limit
            self._conversation_id = generate_pipeline_id()

        def _trim_history(
            self, history: List[ConversationEntry]
        ) -> List[ConversationEntry]:
            if self._history_limit is not None and len(history) > self._history_limit:
                return history[-self._history_limit :]
            return history

        async def process_request(self, user_message: str) -> Dict[str, Any]:
            history = await self._memory.load_conversation(self._conversation_id)
            history.append(
                ConversationEntry(
                    content=user_message, role="user", timestamp=datetime.now()
                )
            )
            history = self._trim_history(history)

            state = PipelineState(
                conversation=list(history),
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

            history = (
                state.conversation[-self._history_limit :]
                if self._history_limit
                else state.conversation
            )
            await self._memory.save_conversation(self._conversation_id, history)

            while (
                isinstance(response, dict)
                and response.get("type") == "continue_processing"
            ):
                follow_up = str(response.get("message", ""))
                history.append(
                    ConversationEntry(
                        content=follow_up, role="user", timestamp=datetime.now()
                    )
                )
                history = self._trim_history(history)
                state = PipelineState(
                    conversation=list(history),
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
                history = (
                    state.conversation[-self._history_limit :]
                    if self._history_limit
                    else state.conversation
                )
                await self._memory.save_conversation(self._conversation_id, history)
            return response

    def start_conversation(
        self,
        registries: SystemRegistries,
        pipeline_manager: PipelineManager | None = None,
        *,
        history_limit: int | None = None,
    ) -> "Memory.ConversationSession":
        if self._conversation_manager is None:
            self._conversation_manager = Memory.ConversationSession(
                self,
                registries,
                pipeline_manager,
                history_limit=history_limit,
            )
        return self._conversation_manager

    # Backwards compatibility
    get_conversation_manager = start_conversation
