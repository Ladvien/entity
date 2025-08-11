"""Example plugins have been moved to entity-plugin-examples package.

This module provides backward compatibility. Please update your imports to use
the new package directly.

Migration:
    Old: from entity.plugins.examples import CalculatorPlugin
    New: from entity_plugin_examples import CalculatorPlugin
"""

import warnings

# Import from compatibility layer
from entity.plugins.examples_compat import *  # noqa: F401, F403

warnings.warn(
    "The entity.plugins.examples module is deprecated. "
    "Please install and import from entity-plugin-examples instead.",
    DeprecationWarning,
    stacklevel=2,
)
