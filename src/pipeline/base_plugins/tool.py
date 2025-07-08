from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Type

from pydantic import BaseModel, ValidationError

from ..errors import ToolExecutionError
from .base import BasePlugin


class ToolPlugin(BasePlugin):
    """Base class for tool plugins executed outside the pipeline."""

    required_params: List[str] = []

    def _validate_required_params(self, params: Dict[str, Any]) -> bool:
        """Ensure all :attr:`required_params` are present in ``params``."""
        missing = [p for p in self.required_params if params.get(p) is None]
        if missing:
            raise ToolExecutionError(
                self.__class__.__name__,
                ValueError(f"Missing required parameters: {', '.join(missing)}"),
            )
        return True

    def validate_tool_params(
        self, params: BaseModel | Dict[str, Any]
    ) -> BaseModel | Dict[str, Any]:
        """Validate ``params`` using ``Params`` model when provided."""

        if isinstance(params, BaseModel):
            return params

        model_cls: Type[BaseModel] | None = getattr(self, "Params", None)
        if model_cls is not None and issubclass(model_cls, BaseModel):
            try:
                return model_cls(**params)
            except ValidationError as exc:  # pragma: no cover - re-raise
                raise ToolExecutionError(self.__class__.__name__, exc) from exc

        self._validate_required_params(params)
        return params

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self.max_retries = int(self.config.get("max_retries", 1))
        self.retry_delay = float(self.config.get("retry_delay", 1.0))

    async def execute(self, params: Dict[str, Any]) -> Any:  # type: ignore[override]
        """Execute the tool and return its result."""
        return await self.execute_function_with_retry(params)

    async def execute_function(self, params: Dict[str, Any]):
        raise NotImplementedError()

    async def execute_function_with_retry(
        self,
        params: Dict[str, Any],
        max_retries: int | None = None,
        delay: float | None = None,
    ):
        validated = self.validate_tool_params(params)
        max_retry_count = self.max_retries if max_retries is None else max_retries
        retry_delay_seconds = self.retry_delay if delay is None else delay
        for attempt in range(max_retry_count + 1):
            try:
                return await self.execute_function(validated)
            except Exception:  # noqa: BLE001
                if attempt == max_retry_count:
                    raise
                await asyncio.sleep(retry_delay_seconds)

    async def execute_with_timeout(
        self, params: Dict[str, Any], timeout: int = 30
    ) -> Any:
        """Execute the tool with a timeout."""
        return await asyncio.wait_for(self.execute(params), timeout=timeout)

    async def _execute_impl(self, context: "PluginContext"):
        """Tools are not executed in the pipeline directly."""
        pass
