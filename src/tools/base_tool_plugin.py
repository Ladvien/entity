# src/tools/base_tool.py

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseToolPlugin(ABC):
    """Abstract base class for tool plugins."""

    name: str
    description: str

    @abstractmethod
    async def run(self, input_data: Dict[str, Any]) -> str: ...

    @abstractmethod
    def get_context_injection(
        self, user_input: str, thread_id: str = "default"
    ) -> Dict[str, Any]:
        """Override to inject variables like memory_context into prompt."""
        raise NotImplementedError(
            "Please implement get_context_injection method in your tool plugin."
        )
