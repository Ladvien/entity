from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Type

from pydantic import BaseModel, ValidationError


class Plugin(ABC):
    """Base class for all plugins."""

    class ConfigModel(BaseModel):
        """Default empty configuration."""

        class Config:  # pragma: no cover - simple pydantic setup
            extra = "forbid"

    stage: str | None = None
    supported_stages: list[str] = []
    dependencies: list[str] = []

    def __init__(self, resources: dict[str, Any], config: Dict[str, Any] | None = None):
        self.resources = resources
        self.config = self.validate_config(config or {})
        self._validate_dependencies()

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> ConfigModel:
        """Return validated configuration for ``cls``."""
        try:
            return cls.ConfigModel(**config)
        except ValidationError as exc:  # pragma: no cover - simple conversion
            raise ValueError(
                f"Invalid configuration for {cls.__name__}: {exc}"
            ) from exc

    @classmethod
    def validate_workflow(cls, stage: str) -> None:
        """Ensure ``cls`` can run at ``stage``."""
        from ..workflow.workflow import WorkflowConfigError

        if cls.supported_stages and stage not in cls.supported_stages:
            allowed = ", ".join(cls.supported_stages)
            raise WorkflowConfigError(
                f"{cls.__name__} does not support stage '{stage}'. "
                f"Supported stages: {allowed}"
            )
        if cls.stage and cls.stage != stage:
            raise WorkflowConfigError(
                f"{cls.__name__} is fixed to stage '{cls.stage}', not '{stage}'"
            )

    async def execute(self, context: Any) -> Any:
        """Validate and run the plugin implementation."""
        self._enforce_stage(context)
        try:
            return await self._execute_impl(context)
        except Exception as exc:  # pragma: no cover - simple example
            raise RuntimeError(
                f"{self.__class__.__name__} failed during execution"
            ) from exc

    def _enforce_stage(self, context: Any) -> None:
        current = getattr(context, "current_stage", None)
        expected = self.stage
        if expected and current != expected:
            raise RuntimeError(
                f"{self.__class__.__name__} expected stage '{expected}' but "
                f"was scheduled for '{current}'"
            )
        if self.supported_stages and current not in self.supported_stages:
            allowed = ", ".join(self.supported_stages)
            raise RuntimeError(
                f"{self.__class__.__name__} does not support stage '{current}'. "
                f"Supported stages: {allowed}"
            )

    def _validate_dependencies(self) -> None:
        missing = [dep for dep in self.dependencies if dep not in self.resources]
        if missing:
            needed = ", ".join(missing)
            raise RuntimeError(
                f"{self.__class__.__name__} requires resources: {needed}"
            )

    @abstractmethod
    async def _execute_impl(self, context: Any) -> Any:
        """Plugin-specific execution logic."""
        raise NotImplementedError
