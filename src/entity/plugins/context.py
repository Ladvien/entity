from __future__ import annotations

from typing import Any, Dict, List

from ..workflow.executor import WorkflowContext


class PluginContext(WorkflowContext):
    """Extended context exposing memory and resources."""

    def __init__(self, resources: Dict[str, Any], user_id: str) -> None:
        super().__init__()
        self._resources = resources
        self.user_id = user_id
        self._memory: Dict[str, Any] = {}
        self._conversation: List[str] = []

    async def remember(self, key: str, value: Any) -> None:
        """Persist value namespaced by ``user_id``."""
        namespaced = f"{self.user_id}:{key}"
        self._memory[namespaced] = value

    async def recall(self, key: str, default: Any | None = None) -> Any:
        """Retrieve stored value for ``key`` or ``default``."""
        namespaced = f"{self.user_id}:{key}"
        return self._memory.get(namespaced, default)

    def say(self, message: str) -> None:  # type: ignore[override]
        super().say(message)
        self._conversation.append(message)

    def listen(self) -> str | None:
        """Return the last user message."""
        return self.message

    def conversation(self) -> List[str]:
        """Return conversation history including outputs."""
        history = list(self._conversation)
        if self.message:
            history.insert(0, self.message)
        return history

    def get_resource(self, name: str) -> Any:
        """Return a resource by name."""
        return self._resources.get(name)
