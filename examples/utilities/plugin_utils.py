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

    # isort: off
    import pipeline.user_plugins
    import pipeline.user_plugins.resources as plugin_resources
    import pipeline.resources

    # isort: on

    plugins_mod.__dict__.update(vars(pipeline.user_plugins))
    sys.modules["user_plugins.resources"] = plugin_resources
    plugins_mod.resources = plugin_resources

    for _, name, _ in pkgutil.walk_packages(
        pipeline.resources.__path__, prefix="pipeline.resources."
    ):
        module = importlib.import_module(name)
        alias = name.replace("pipeline.resources.", "user_plugins.")
        sys.modules[alias] = module
        parent_alias = alias.rsplit(".", 1)[0]
        if parent_alias == "plugins":
            setattr(plugins_mod, alias.split(".")[-1], module)
        else:
            parent = sys.modules.setdefault(
                parent_alias, types.ModuleType(parent_alias)
            )
            setattr(parent, alias.split(".")[-1], module)
