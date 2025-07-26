from __future__ import annotations

import pytest
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from entity.plugins import Plugin  # noqa: F401
from entity.workflow.workflow import Workflow, WorkflowConfigError


class PluginValidationTests:
    """Mixin with basic validation checks for plugins."""

    Plugin: type[Plugin]
    stage: str = "think"
    config: dict = {}
    resources: dict = {} # Add resources for plugin instantiation

    def test_validate_config(self):
        plugin_instance = self.Plugin(self.resources, self.config)
        result = plugin_instance.validate_config()
        assert result.success

    def test_validate_workflow(self):
        plugin_instance = self.Plugin(self.resources, self.config)
        # Create a dummy workflow for validation
        dummy_workflow = Workflow(steps={self.stage: [plugin_instance]}, supported_stages=[self.stage])
        plugin_instance.assigned_stage = self.stage
        result = plugin_instance.validate_workflow(dummy_workflow)
        assert result.success

    def test_invalid_stage(self):
        plugin_instance = self.Plugin(self.resources, self.config)
        # Create a dummy workflow that does not support the assigned stage
        dummy_workflow = Workflow(steps={}, supported_stages=["another_stage"])
        plugin_instance.assigned_stage = self.stage # Manually assign stage for this test
        result = plugin_instance.validate_workflow(dummy_workflow)
        assert not result.success
        assert "Workflow does not support stage" in result.errors[0]


class PluginDependencyTests:
    """Mixin verifying dependency checks during initialization."""

    Plugin: type[Plugin]
    resources: dict = {}
    config: dict = {}

    def test_missing_dependency_error(self):
        if not self.Plugin.dependencies:
            pytest.skip("plugin has no dependencies")
        partial_resources = {d: object() for d in self.Plugin.dependencies[:-1]}
        with pytest.raises(RuntimeError, match="missing required resources"):
            self.Plugin(partial_resources, config=self.config)
