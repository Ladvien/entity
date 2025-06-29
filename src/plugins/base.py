from abc import ABC, abstractmethod
from typing import Any, Dict, Type

from langchain_core.tools import StructuredTool
from pydantic import BaseModel


class BaseToolPlugin(ABC):
    use_registry: bool = True

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @property
    @abstractmethod
    def args_schema(self) -> Type[BaseModel]: ...

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
            coroutine=self.run,
        )
