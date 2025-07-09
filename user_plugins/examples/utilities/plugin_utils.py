"""Utility helpers for example scripts."""

from __future__ import annotations

import importlib
import importlib.machinery
import pathlib
import pkgutil
import sys
import types


def enable_plugins_namespace() -> None:
    """Expose ``plugins`` namespace for local examples.

    The examples ship plugins under the ``plugins`` directory instead of an
    installed package. This helper inserts that directory into ``sys.modules``
    so imports like ``from plugins.my_plugin import MyPlugin`` work without
    additional configuration. It also maps built-in pipeline resources under
    ``user_plugins.*`` for convenience.
    """

    plugins_mod = types.ModuleType("plugins")
    plugins_mod.__path__ = [
        str(pathlib.Path(__file__).resolve().parents[2] / "plugins")
    ]
    plugins_mod.__spec__ = importlib.machinery.ModuleSpec(
        "plugins", None, is_package=True
    )
    sys.modules["plugins"] = plugins_mod

    from entity.core import plugins as core_plugins

    plugins_mod.__dict__.update(vars(core_plugins))
