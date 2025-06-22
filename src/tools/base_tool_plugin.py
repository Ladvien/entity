from abc import ABC, abstractmethod
from typing import Any, Dict
from pydantic import BaseModel
from langchain_core.tools import StructuredTool


class BaseToolPlugin(ABC):
    """Abstract base class for tool plugins."""

    name: str
    description: str
    args_schema: type

    @abstractmethod
    async def run(self, input_data: BaseModel) -> str: ...

    @abstractmethod
    def get_context_injection(
        self, user_input: str, thread_id: str = "default"
    ) -> Dict[str, Any]: ...

    def as_tool(self) -> StructuredTool:
        return StructuredTool(
            name=self.name,
            description=self.description,
            args_schema=self.args_schema,
            func=self.run,  # async function OK
        )
