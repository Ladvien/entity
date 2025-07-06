"""Compatibility shim for renamed package."""

import sys
from importlib import import_module

module = import_module("src.entity_config")

# re-export attributes
__all__ = getattr(module, "__all__", [])
for attr in __all__:
    globals()[attr] = getattr(module, attr)

# expose submodules
for name in (
    "builder",
    "environment",
    "generate_template",
    "migrate",
    "models",
    "validator",
    "validators",
):
    sys.modules[f"{__name__}.{name}"] = import_module(f"src.entity_config.{name}")
