# src/tools/base_tool.py

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseToolPlugin(ABC):
    """Abstract base class for tool plugins."""

    name: str
    description: str

    @abstractmethod
    async def run(self, input_data: Dict[str, Any]) -> str: ...
