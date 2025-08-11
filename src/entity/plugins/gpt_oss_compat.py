"""
Backward compatibility shims for GPT-OSS plugins.

These shims provide backward compatibility for code that imports GPT-OSS plugins
from the original location (entity.plugins.gpt_oss). The plugins have been moved
to a separate package (entity-plugin-gpt-oss) as part of the modularization effort.

This compatibility layer will be deprecated in a future version.
"""

import warnings
from typing import Any

# Deprecation warning message
DEPRECATION_MESSAGE = (
    "Importing GPT-OSS plugins from 'entity.plugins.gpt_oss' is deprecated. "
    "Please install 'entity-plugin-gpt-oss' and import from 'entity_plugin_gpt_oss' instead. "
    "This compatibility layer will be removed in entity-core 0.1.0."
)


def _warn_deprecated_import(plugin_name: str) -> None:
    """Issue deprecation warning for old imports."""
    warnings.warn(
        f"{plugin_name}: {DEPRECATION_MESSAGE}", DeprecationWarning, stacklevel=3
    )


class _CompatibilityShim:
    """Base class for compatibility shims."""

    def __init__(self, plugin_class_name: str, new_module_path: str):
        self.plugin_class_name = plugin_class_name
        self.new_module_path = new_module_path
        self._plugin_class = None

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Create plugin instance with deprecation warning."""
        _warn_deprecated_import(self.plugin_class_name)

        if self._plugin_class is None:
            try:
                module = __import__(
                    self.new_module_path, fromlist=[self.plugin_class_name]
                )
                self._plugin_class = getattr(module, self.plugin_class_name)
            except ImportError as e:
                raise ImportError(
                    f"Failed to import {self.plugin_class_name} from {self.new_module_path}. "
                    f"Please install 'entity-plugin-gpt-oss' package: pip install entity-plugin-gpt-oss"
                ) from e

        return self._plugin_class(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        """Forward attribute access to the actual plugin class."""
        _warn_deprecated_import(self.plugin_class_name)

        if self._plugin_class is None:
            try:
                module = __import__(
                    self.new_module_path, fromlist=[self.plugin_class_name]
                )
                self._plugin_class = getattr(module, self.plugin_class_name)
            except ImportError as e:
                raise ImportError(
                    f"Failed to import {self.plugin_class_name} from {self.new_module_path}. "
                    f"Please install 'entity-plugin-gpt-oss' package: pip install entity-plugin-gpt-oss"
                ) from e

        return getattr(self._plugin_class, name)


# Create compatibility shims for all GPT-OSS plugins
ReasoningTracePlugin = _CompatibilityShim(
    "ReasoningTracePlugin", "entity_plugin_gpt_oss.reasoning_trace"
)

StructuredOutputPlugin = _CompatibilityShim(
    "StructuredOutputPlugin", "entity_plugin_gpt_oss.structured_output"
)

DeveloperOverridePlugin = _CompatibilityShim(
    "DeveloperOverridePlugin", "entity_plugin_gpt_oss.developer_override"
)

AdaptiveReasoningPlugin = _CompatibilityShim(
    "AdaptiveReasoningPlugin", "entity_plugin_gpt_oss.adaptive_reasoning"
)

GPTOSSToolOrchestrator = _CompatibilityShim(
    "GPTOSSToolOrchestrator", "entity_plugin_gpt_oss.native_tools"
)

MultiChannelAggregatorPlugin = _CompatibilityShim(
    "MultiChannelAggregatorPlugin", "entity_plugin_gpt_oss.multi_channel_aggregator"
)

HarmonySafetyFilterPlugin = _CompatibilityShim(
    "HarmonySafetyFilterPlugin", "entity_plugin_gpt_oss.harmony_safety_filter"
)

FunctionSchemaRegistryPlugin = _CompatibilityShim(
    "FunctionSchemaRegistryPlugin", "entity_plugin_gpt_oss.function_schema_registry"
)

ReasoningAnalyticsDashboardPlugin = _CompatibilityShim(
    "ReasoningAnalyticsDashboardPlugin",
    "entity_plugin_gpt_oss.reasoning_analytics_dashboard",
)


# Module-level imports for helper classes and enums
def __getattr__(name: str) -> Any:
    """
    Dynamic import for helper classes and enums from the GPT-OSS package.

    This allows importing not just plugin classes but also helper classes
    like ReasoningLevel, ReasoningTrace, etc. that are used by the tests.
    """

    # Mapping of helper class names to their module locations
    helper_class_mapping = {
        # From reasoning_trace.py
        "ReasoningLevel": "entity_plugin_gpt_oss.reasoning_trace",
        "ReasoningTrace": "entity_plugin_gpt_oss.reasoning_trace",
        # From structured_output.py
        "OutputFormat": "entity_plugin_gpt_oss.structured_output",
        "ValidationResult": "entity_plugin_gpt_oss.structured_output",
        # From developer_override.py
        "DeveloperOverride": "entity_plugin_gpt_oss.developer_override",
        "OverrideScope": "entity_plugin_gpt_oss.developer_override",
        "PermissionLevel": "entity_plugin_gpt_oss.developer_override",
        # From adaptive_reasoning.py
        "ReasoningEffort": "entity_plugin_gpt_oss.adaptive_reasoning",
        "ComplexityFactors": "entity_plugin_gpt_oss.adaptive_reasoning",
        "ComplexityScore": "entity_plugin_gpt_oss.adaptive_reasoning",
        "ReasoningDecision": "entity_plugin_gpt_oss.adaptive_reasoning",
        "PerformanceMetrics": "entity_plugin_gpt_oss.adaptive_reasoning",
        # From native_tools.py
        "ToolExecutionContext": "entity_plugin_gpt_oss.native_tools",
        "ToolResult": "entity_plugin_gpt_oss.native_tools",
        # From multi_channel_aggregator.py
        "ChannelConfig": "entity_plugin_gpt_oss.multi_channel_aggregator",
        "AggregationStrategy": "entity_plugin_gpt_oss.multi_channel_aggregator",
        # From harmony_safety_filter.py
        "SafetyLevel": "entity_plugin_gpt_oss.harmony_safety_filter",
        "FilterResult": "entity_plugin_gpt_oss.harmony_safety_filter",
        # From function_schema_registry.py
        "FunctionSchema": "entity_plugin_gpt_oss.function_schema_registry",
        "SchemaValidation": "entity_plugin_gpt_oss.function_schema_registry",
        # From reasoning_analytics_dashboard.py
        "AnalyticsMetric": "entity_plugin_gpt_oss.reasoning_analytics_dashboard",
        "DashboardConfig": "entity_plugin_gpt_oss.reasoning_analytics_dashboard",
    }

    if name in helper_class_mapping:
        _warn_deprecated_import(name)

        try:
            module_path = helper_class_mapping[name]
            module = __import__(module_path, fromlist=[name])
            return getattr(module, name)
        except ImportError as e:
            raise ImportError(
                f"Failed to import {name} from {module_path}. "
                f"Please install 'entity-plugin-gpt-oss' package: pip install entity-plugin-gpt-oss"
            ) from e

    # If not found in helper classes, raise AttributeError
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# Export all plugin classes
# Helper classes are handled by __getattr__ and don't need to be in __all__
__all__ = [
    "ReasoningTracePlugin",
    "StructuredOutputPlugin",
    "DeveloperOverridePlugin",
    "AdaptiveReasoningPlugin",
    "GPTOSSToolOrchestrator",
    "MultiChannelAggregatorPlugin",
    "HarmonySafetyFilterPlugin",
    "FunctionSchemaRegistryPlugin",
    "ReasoningAnalyticsDashboardPlugin",
]
