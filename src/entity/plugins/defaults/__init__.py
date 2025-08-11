from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from entity.plugins.base import Plugin
from entity.workflow.executor import WorkflowExecutor
from entity.workflow.workflow import Workflow


class PassThroughPlugin(Plugin):
    """Unified plugin that passes messages through with optional stage-specific behavior.

    This plugin consolidates the functionality of the previous 6 separate default plugins
    (InputPlugin, ParsePlugin, ThinkPlugin, DoPlugin, ReviewPlugin, OutputPlugin) into
    a single configurable plugin to reduce code duplication and memory usage.
    """

    class ConfigModel(BaseModel):
        """Configuration for PassThroughPlugin."""

        stage: str
        enable_output_say: bool = True  # Whether to call context.say() for OUTPUT stage

    def __init__(self, resources: dict[str, Any], config: dict[str, Any] | None = None):
        super().__init__(resources, config)

        # Validate and parse config using Pydantic
        validation_result = self.validate_config()
        if not validation_result.success:
            raise ValueError(
                f"PassThroughPlugin configuration validation failed: {', '.join(validation_result.errors)}"
            )

        # Validate stage value
        stage = self.config.stage
        valid_stages = [
            WorkflowExecutor.INPUT,
            WorkflowExecutor.PARSE,
            WorkflowExecutor.THINK,
            WorkflowExecutor.DO,
            WorkflowExecutor.REVIEW,
            WorkflowExecutor.OUTPUT,
        ]

        if stage not in valid_stages:
            raise ValueError(f"Invalid stage '{stage}'. Must be one of: {valid_stages}")

        # Set supported_stages dynamically based on configuration
        self.supported_stages = [stage]

    async def _execute_impl(self, context) -> str:
        """Execute stage-specific behavior."""
        message = context.message or ""

        # Special handling for OUTPUT stage
        if (
            self.config.stage == WorkflowExecutor.OUTPUT
            and self.config.enable_output_say
        ):
            context.say(message)

        return message


# Factory functions for backward compatibility
def InputPlugin(
    resources: dict[str, Any], config: dict[str, Any] | None = None
) -> PassThroughPlugin:
    """Factory function for INPUT stage plugin. DEPRECATED: Use PassThroughPlugin directly."""
    merged_config = {"stage": WorkflowExecutor.INPUT}
    if config:
        merged_config.update(config)
    return PassThroughPlugin(resources, merged_config)


def ParsePlugin(
    resources: dict[str, Any], config: dict[str, Any] | None = None
) -> PassThroughPlugin:
    """Factory function for PARSE stage plugin. DEPRECATED: Use PassThroughPlugin directly."""
    merged_config = {"stage": WorkflowExecutor.PARSE}
    if config:
        merged_config.update(config)
    return PassThroughPlugin(resources, merged_config)


def ThinkPlugin(
    resources: dict[str, Any], config: dict[str, Any] | None = None
) -> PassThroughPlugin:
    """Factory function for THINK stage plugin. DEPRECATED: Use PassThroughPlugin directly."""
    merged_config = {"stage": WorkflowExecutor.THINK}
    if config:
        merged_config.update(config)
    return PassThroughPlugin(resources, merged_config)


def DoPlugin(
    resources: dict[str, Any], config: dict[str, Any] | None = None
) -> PassThroughPlugin:
    """Factory function for DO stage plugin. DEPRECATED: Use PassThroughPlugin directly."""
    merged_config = {"stage": WorkflowExecutor.DO}
    if config:
        merged_config.update(config)
    return PassThroughPlugin(resources, merged_config)


def ReviewPlugin(
    resources: dict[str, Any], config: dict[str, Any] | None = None
) -> PassThroughPlugin:
    """Factory function for REVIEW stage plugin. DEPRECATED: Use PassThroughPlugin directly."""
    merged_config = {"stage": WorkflowExecutor.REVIEW}
    if config:
        merged_config.update(config)
    return PassThroughPlugin(resources, merged_config)


def OutputPlugin(
    resources: dict[str, Any], config: dict[str, Any] | None = None
) -> PassThroughPlugin:
    """Factory function for OUTPUT stage plugin. DEPRECATED: Use PassThroughPlugin directly."""
    merged_config = {"stage": WorkflowExecutor.OUTPUT, "enable_output_say": True}
    if config:
        merged_config.update(config)
    return PassThroughPlugin(resources, merged_config)


def default_workflow(resources: dict[str, Any]) -> Workflow:
    """Return the built-in workflow with one plugin per stage."""
    steps = {
        WorkflowExecutor.INPUT: [InputPlugin(resources)],
        WorkflowExecutor.PARSE: [ParsePlugin(resources)],
        WorkflowExecutor.THINK: [ThinkPlugin(resources)],
        WorkflowExecutor.DO: [DoPlugin(resources)],
        WorkflowExecutor.REVIEW: [ReviewPlugin(resources)],
        WorkflowExecutor.OUTPUT: [OutputPlugin(resources)],
    }
    return Workflow(steps, WorkflowExecutor._STAGES)
