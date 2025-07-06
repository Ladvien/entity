from __future__ import annotations

"""Compatibility package mapping to ``plugins.contrib``."""

import sys
from importlib import import_module

for _sub in ["failure", "resources", "prompts", "tools", "infrastructure"]:
    try:
        mod = import_module(f"plugins.contrib.{_sub}")
    except ModuleNotFoundError:
        continue
    sys.modules[f"user_plugins.{_sub}"] = mod
