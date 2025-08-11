"""
Backward compatibility shims for GPT-OSS plugins.

These shims provide backward compatibility for code that imports GPT-OSS plugins
from the original location (entity.plugins.gpt_oss). The plugins have been moved
to a separate package (entity-plugin-gpt-oss) as part of the modularization effort.

====================================================================================
                            MIGRATION GUIDE
====================================================================================

DEPRECATED: The entity.plugins.gpt_oss module is deprecated and will be removed
            in entity-core 0.1.0 (target: Q2 2024)

OLD WAY (Deprecated):
    from entity.plugins.gpt_oss import ReasoningTracePlugin

NEW WAY (Recommended):
    1. Install the new package:
       pip install entity-plugin-gpt-oss

    2. Update your imports:
       from entity_plugin_gpt_oss import ReasoningTracePlugin

AFFECTED PLUGINS:
    - ReasoningTracePlugin
    - StructuredOutputPlugin
    - DeveloperOverridePlugin
    - AdaptiveReasoningPlugin
    - GPTOSSToolOrchestrator
    - MultiChannelAggregatorPlugin
    - HarmonySafetyFilterPlugin
    - FunctionSchemaRegistryPlugin
    - ReasoningAnalyticsDashboardPlugin

SUPPRESSING WARNINGS:
    For CI/CD systems, set the environment variable:
    ENTITY_SUPPRESS_GPT_OSS_DEPRECATION=1

NEED HELP?
    - Documentation: https://entity-framework.readthedocs.io/migration
    - Issues: https://github.com/entity-framework/entity-core/issues

====================================================================================
"""

import importlib.util
import logging
import os
import warnings
from typing import Any, Optional

# Set up logging
logger = logging.getLogger(__name__)

# Check if we should suppress deprecation warnings (for CI/CD)
SUPPRESS_DEPRECATION = os.environ.get(
    "ENTITY_SUPPRESS_GPT_OSS_DEPRECATION", ""
).lower() in (
    "1",
    "true",
    "yes",
)

# Deprecation timeline
DEPRECATION_VERSION = "0.1.0"
DEPRECATION_DATE = "Q2 2024"

# Package name for the new GPT-OSS plugin package
GPT_OSS_PACKAGE = "entity-plugin-gpt-oss"
GPT_OSS_MODULE = "entity_plugin_gpt_oss"


def _check_package_installed() -> bool:
    """Check if entity-plugin-gpt-oss package is installed."""
    spec = importlib.util.find_spec(GPT_OSS_MODULE)
    return spec is not None


def _get_package_version() -> Optional[str]:
    """Get the version of entity-plugin-gpt-oss if installed."""
    try:
        import importlib.metadata

        return importlib.metadata.version(GPT_OSS_PACKAGE)
    except (ImportError, importlib.metadata.PackageNotFoundError):
        return None


def _create_detailed_error_message(
    plugin_name: str, module_path: str, original_error: Exception
) -> str:
    """Create a detailed error message with migration instructions."""
    package_installed = _check_package_installed()
    package_version = _get_package_version()

    if not package_installed:
        return (
            f"\n"
            f"╔══════════════════════════════════════════════════════════════════════╗\n"
            f"║                     GPT-OSS Plugin Not Available                      ║\n"
            f"╚══════════════════════════════════════════════════════════════════════╝\n"
            f"\n"
            f"The '{plugin_name}' plugin requires the 'entity-plugin-gpt-oss' package.\n"
            f"\n"
            f"To fix this issue:\n"
            f"\n"
            f"1. Install the package:\n"
            f"   pip install entity-plugin-gpt-oss\n"
            f"\n"
            f"2. Update your import statements:\n"
            f"   OLD: from entity.plugins.gpt_oss import {plugin_name}\n"
            f"   NEW: from entity_plugin_gpt_oss import {plugin_name}\n"
            f"\n"
            f"3. Or add to your requirements.txt:\n"
            f"   entity-plugin-gpt-oss>=0.1.0\n"
            f"\n"
            f"Note: The old import path (entity.plugins.gpt_oss) is deprecated\n"
            f"      and will be removed in entity-core {DEPRECATION_VERSION} ({DEPRECATION_DATE}).\n"
            f"\n"
            f"Original error: {original_error}\n"
        )
    else:
        return (
            f"\n"
            f"╔══════════════════════════════════════════════════════════════════════╗\n"
            f"║                    GPT-OSS Plugin Import Error                        ║\n"
            f"╚══════════════════════════════════════════════════════════════════════╝\n"
            f"\n"
            f"Failed to import '{plugin_name}' from '{module_path}'.\n"
            f"\n"
            f"Package status:\n"
            f"  - entity-plugin-gpt-oss: Installed (version {package_version})\n"
            f"  - Module path: {module_path}\n"
            f"\n"
            f"This might be due to:\n"
            f"  1. Version incompatibility\n"
            f"  2. Corrupted installation\n"
            f"  3. Missing dependencies\n"
            f"\n"
            f"Try reinstalling:\n"
            f"   pip install --upgrade --force-reinstall entity-plugin-gpt-oss\n"
            f"\n"
            f"Original error: {original_error}\n"
        )


def _warn_deprecated_import(plugin_name: str) -> None:
    """Issue deprecation warning for old imports with logging."""
    if SUPPRESS_DEPRECATION:
        return

    message = (
        f"Importing '{plugin_name}' from 'entity.plugins.gpt_oss' is deprecated "
        f"and will be removed in entity-core {DEPRECATION_VERSION} ({DEPRECATION_DATE}). "
        f"Please install 'entity-plugin-gpt-oss' and import from 'entity_plugin_gpt_oss' instead. "
        f"To suppress this warning, set ENTITY_SUPPRESS_GPT_OSS_DEPRECATION=1"
    )

    # Issue standard deprecation warning
    warnings.warn(message, DeprecationWarning, stacklevel=3)

    # Also log the deprecation
    logger.warning(f"DEPRECATION: {message}")


class _CompatibilityShim:
    """Base class for compatibility shims with enhanced error handling."""

    def __init__(self, plugin_class_name: str, new_module_path: str):
        self.plugin_class_name = plugin_class_name
        self.new_module_path = new_module_path
        self._plugin_class = None
        self._import_error = None
        self._attempted_import = False

    def _try_import(self) -> bool:
        """Attempt to import the plugin class."""
        if self._attempted_import:
            return self._plugin_class is not None

        self._attempted_import = True

        try:
            # Log the import attempt
            logger.debug(
                f"Attempting to import {self.plugin_class_name} from {self.new_module_path}"
            )

            module = __import__(self.new_module_path, fromlist=[self.plugin_class_name])
            self._plugin_class = getattr(module, self.plugin_class_name)

            logger.debug(f"Successfully imported {self.plugin_class_name}")
            return True

        except Exception as e:
            self._import_error = e
            logger.error(
                f"Failed to import {self.plugin_class_name}: {e}", exc_info=True
            )
            return False

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Create plugin instance with deprecation warning and fallback."""
        _warn_deprecated_import(self.plugin_class_name)

        if not self._try_import():
            # Provide detailed error message
            error_msg = _create_detailed_error_message(
                self.plugin_class_name, self.new_module_path, self._import_error
            )
            raise ImportError(error_msg) from self._import_error

        return self._plugin_class(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        """Forward attribute access to the actual plugin class."""
        _warn_deprecated_import(self.plugin_class_name)

        if not self._try_import():
            # Check for common attributes to provide better errors
            if name in ["__name__", "__module__", "__doc__"]:
                # Return placeholder values for introspection
                return f"Unavailable({self.plugin_class_name})"

            # Provide detailed error message
            error_msg = _create_detailed_error_message(
                self.plugin_class_name, self.new_module_path, self._import_error
            )
            raise ImportError(error_msg) from self._import_error

        return getattr(self._plugin_class, name)

    def __repr__(self) -> str:
        """Return a representation of the shim."""
        if self._plugin_class is not None:
            return f"<CompatibilityShim for {self._plugin_class}>"
        else:
            return f"<CompatibilityShim for {self.plugin_class_name} (not available)>"


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
        "AuditEntry": "entity_plugin_gpt_oss.developer_override",
        # From adaptive_reasoning.py
        "ReasoningEffort": "entity_plugin_gpt_oss.adaptive_reasoning",
        "ComplexityFactors": "entity_plugin_gpt_oss.adaptive_reasoning",
        "ComplexityScore": "entity_plugin_gpt_oss.adaptive_reasoning",
        "ReasoningDecision": "entity_plugin_gpt_oss.adaptive_reasoning",
        "PerformanceMetrics": "entity_plugin_gpt_oss.adaptive_reasoning",
        # From native_tools.py
        "ToolExecutionContext": "entity_plugin_gpt_oss.native_tools",
        "ToolResult": "entity_plugin_gpt_oss.native_tools",
        "ToolConfig": "entity_plugin_gpt_oss.native_tools",
        "ToolExecutionMode": "entity_plugin_gpt_oss.native_tools",
        "ToolInvocation": "entity_plugin_gpt_oss.native_tools",
        "ToolChain": "entity_plugin_gpt_oss.native_tools",
        "RateLimiter": "entity_plugin_gpt_oss.native_tools",
        "PythonTool": "entity_plugin_gpt_oss.native_tools",
        "BrowserTool": "entity_plugin_gpt_oss.native_tools",
        # From multi_channel_aggregator.py
        "ChannelConfig": "entity_plugin_gpt_oss.multi_channel_aggregator",
        "AggregationStrategy": "entity_plugin_gpt_oss.multi_channel_aggregator",
        "ChannelContent": "entity_plugin_gpt_oss.multi_channel_aggregator",
        "ChannelType": "entity_plugin_gpt_oss.multi_channel_aggregator",
        "AggregatedResponse": "entity_plugin_gpt_oss.multi_channel_aggregator",
        # From harmony_safety_filter.py
        "SafetyLevel": "entity_plugin_gpt_oss.harmony_safety_filter",
        "FilterResult": "entity_plugin_gpt_oss.harmony_safety_filter",
        "SafetyCategory": "entity_plugin_gpt_oss.harmony_safety_filter",
        "SafetyFilterResult": "entity_plugin_gpt_oss.harmony_safety_filter",
        "SafetySeverity": "entity_plugin_gpt_oss.harmony_safety_filter",
        "SafetyViolation": "entity_plugin_gpt_oss.harmony_safety_filter",
        # From function_schema_registry.py
        "FunctionSchema": "entity_plugin_gpt_oss.function_schema_registry",
        "SchemaValidation": "entity_plugin_gpt_oss.function_schema_registry",
        "FunctionParameter": "entity_plugin_gpt_oss.function_schema_registry",
        "FunctionRegistration": "entity_plugin_gpt_oss.function_schema_registry",
        "FunctionDiscoveryResult": "entity_plugin_gpt_oss.function_schema_registry",
        "ParameterType": "entity_plugin_gpt_oss.function_schema_registry",
        "SchemaFormat": "entity_plugin_gpt_oss.function_schema_registry",
        "ValidationMode": "entity_plugin_gpt_oss.function_schema_registry",
        # From reasoning_analytics_dashboard.py
        "AnalyticsMetric": "entity_plugin_gpt_oss.reasoning_analytics_dashboard",
        "DashboardConfig": "entity_plugin_gpt_oss.reasoning_analytics_dashboard",
        "ReasoningMetrics": "entity_plugin_gpt_oss.reasoning_analytics_dashboard",
    }

    if name in helper_class_mapping:
        _warn_deprecated_import(name)

        try:
            module_path = helper_class_mapping[name]
            logger.debug(f"Attempting to import helper class {name} from {module_path}")

            module = __import__(module_path, fromlist=[name])
            result = getattr(module, name)

            logger.debug(f"Successfully imported helper class {name}")
            return result

        except ImportError as e:
            logger.error(f"Failed to import helper class {name}: {e}", exc_info=True)

            # Provide detailed error message
            error_msg = _create_detailed_error_message(
                name, helper_class_mapping[name], e
            )
            raise ImportError(error_msg) from e

    # If not found in helper classes, raise AttributeError
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# Log module initialization
if _check_package_installed():
    version = _get_package_version()
    logger.info(
        f"GPT-OSS compatibility layer initialized. "
        f"entity-plugin-gpt-oss version {version} is installed."
    )
else:
    logger.warning(
        "GPT-OSS compatibility layer initialized. "
        "entity-plugin-gpt-oss is NOT installed. "
        "Plugins will not be available until the package is installed."
    )

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
