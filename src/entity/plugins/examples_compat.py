"""Compatibility layer for example plugins migration.

This module provides backward compatibility for the example plugins that have been
moved to the entity-plugin-examples package. All imports should be updated to use
the new package directly.

Migration Guide:
    Old: from entity.plugins.examples import CalculatorPlugin
    New: from entity_plugin_examples import CalculatorPlugin

The compatibility layer will be removed in entity-core 0.2.0.
"""

import warnings
from typing import TYPE_CHECKING

# Check if the new package is available
try:
    import entity_plugin_examples

    _PACKAGE_AVAILABLE = True
except ImportError:
    _PACKAGE_AVAILABLE = False
    entity_plugin_examples = None

if TYPE_CHECKING or _PACKAGE_AVAILABLE:
    from entity_plugin_examples import (
        CalculatorPlugin,
        InputReaderPlugin,
        KeywordExtractorPlugin,
        OutputFormatterPlugin,
        ReasonGeneratorPlugin,
        StaticReviewerPlugin,
        TypedExamplePlugin,
    )


def _emit_deprecation_warning(plugin_name: str) -> None:
    """Emit a deprecation warning for plugin imports."""
    warnings.warn(
        f"Importing {plugin_name} from entity.plugins.examples is deprecated. "
        f"Please install entity-plugin-examples and import from there instead. "
        f"Install with: pip install entity-plugin-examples",
        DeprecationWarning,
        stacklevel=3,
    )


# Export all plugins with deprecation warnings
__all__ = [
    "CalculatorPlugin",
    "InputReaderPlugin",
    "KeywordExtractorPlugin",
    "OutputFormatterPlugin",
    "ReasonGeneratorPlugin",
    "StaticReviewerPlugin",
    "TypedExamplePlugin",
]


def __getattr__(name):
    """Lazy import with deprecation warning."""
    if name in __all__:
        _emit_deprecation_warning(name)
        if not _PACKAGE_AVAILABLE:
            raise ImportError(
                f"Cannot import {name}. The entity-plugin-examples package is not installed. "
                f"Install it with: pip install entity-plugin-examples"
            )
        return getattr(entity_plugin_examples, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
