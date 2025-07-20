"""Alias to `user_plugins` for backward compatibility."""

import importlib
import sys

_submodules = [
    "prompts",
    "responders",
    "resources",
    "tools",
    "infrastructure",
    "failure",
]

for _name in _submodules:
    sys.modules[f"{__name__}.{_name}"] = importlib.import_module(
        f"user_plugins.{_name}"
    )
