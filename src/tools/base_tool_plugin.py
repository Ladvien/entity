from abc import ABC, abstractmethod
from typing import Any, Dict, Type
from pydantic import BaseModel
from langchain_core.tools import StructuredTool


class BaseToolPlugin(ABC):
    def __init__(self):
        self._use_count = 0

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @property
    @abstractmethod
    def args_schema(self) -> Type[BaseModel]: ...

    @property
    def max_uses_per_tool(self) -> int:
        return 2

    def check_limit(self) -> bool:
        return self._use_count < self.max_uses_per_tool

    def increment_use(self):
        self._use_count += 1

    @abstractmethod
    async def run(self, input_data: BaseModel) -> str: ...

    @abstractmethod
    def get_context_injection(
        self, user_input: str, thread_id: str = "default"
    ) -> Dict[str, Any]: ...

    def as_tool(self) -> StructuredTool:
        async def limited_run(input_data: BaseModel) -> str:
            if not self.check_limit():
                return f"Tool '{self.name}' has reached its usage limit ({self.max_uses_per_tool})."
            self.increment_use()
            return await self.run(input_data)

        return StructuredTool(
            name=self.name,
            description=f"{self.description} (Max {self.max_uses_per_tool} uses)",
            args_schema=self.args_schema,
            coroutine=limited_run,
        )
