from __future__ import annotations

import pytest
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from entity.plugins import Plugin  # noqa: F401
from entity.workflow.executor import WorkflowExecutor
from entity.workflow.workflow import WorkflowConfigError


class PluginValidationTests:
    """Mixin with basic validation checks for plugins."""

    Plugin: type[Plugin]
    stage: str = WorkflowExecutor.THINK
    config: dict = {}

    def test_validate_config(self):
        self.Plugin.validate_config(self.config)

    def test_validate_workflow(self):
        self.Plugin.validate_workflow(self.stage)

    def test_invalid_stage(self):
        with pytest.raises(WorkflowConfigError, match="cannot"):
            self.Plugin.validate_workflow("invalid")


class PluginDependencyTests:
    """Mixin verifying dependency checks during initialization."""

    Plugin: type[Plugin]
    resources: dict = {}
    config: dict = {}

    def test_missing_dependency_error(self):
        if not self.Plugin.dependencies:
            pytest.skip("plugin has no dependencies")
        partial = {d: object() for d in self.Plugin.dependencies[:-1]}
        with pytest.raises(RuntimeError, match="missing required resources"):
            self.Plugin(partial, config=self.config)
