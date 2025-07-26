from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, TYPE_CHECKING

from pydantic import BaseModel, ValidationError
from entity.plugins.validation import ValidationResult

if TYPE_CHECKING:
    from entity.workflow.workflow import Workflow


class Plugin(ABC):
    """Base class for all plugins."""

    class ConfigModel(BaseModel):
        """Default empty configuration."""

        class Config:
            extra = "forbid"

    supported_stages: list[str] = []
    dependencies: list[str] = []

    def __init__(self, resources: dict[str, Any], config: Dict[str, Any] | None = None):
        """Instantiate the plugin and run all startup validations."""
        self.resources = resources
        self.config = config or {}
        self.assigned_stage: str | None = None
        self._validate_dependencies()

    def validate_config(self) -> ValidationResult:
        """Validate ``config`` using ``ConfigModel`` and return the model."""
        try:
            self.config = self.ConfigModel(**self.config)
            return ValidationResult.success()
        except ValidationError as exc:
            return ValidationResult.error(str(exc))

    def validate_workflow(self, workflow: "Workflow") -> ValidationResult:
        """Validate that ``cls`` can run in ``stage`` before workflow execution."""
        if self.assigned_stage not in workflow.supported_stages:
            return ValidationResult.error(f"Workflow does not support stage {self.assigned_stage}")
        return ValidationResult.success()

    async def execute(self, context: Any) -> Any:
        """Run the plugin."""
        if context.current_stage not in self.supported_stages:
            raise RuntimeError(f"Plugin cannot run in {context.current_stage}")

        context._current_plugin_name = self.__class__.__name__

        return await self._execute_impl(context)

    def _validate_dependencies(self) -> None:
        missing = [dep for dep in self.dependencies if dep not in self.resources]
        if missing:
            needed = ", ".join(missing)
            raise RuntimeError(
                f"{self.__class__.__name__} missing required resources: {needed}"
            )

    @abstractmethod
    async def _execute_impl(self, context: Any) -> Any:
        """Plugin-specific execution logic."""
        raise NotImplementedError
