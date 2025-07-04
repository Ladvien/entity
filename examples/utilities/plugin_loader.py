"""Example showing Agent.from_directory error handling."""

from __future__ import annotations

import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "src"))


def _enable_plugins_namespace() -> None:
    import importlib
    import pkgutil
    import types

    plugins_mod = types.ModuleType("plugins")
    plugins_mod.__path__ = [
        str(pathlib.Path(__file__).resolve().parents[2] / "plugins")
    ]
    import importlib.machinery

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


_enable_plugins_namespace()

from entity import Agent  # noqa: E402
from plugins.adapters.server import AgentServer  # noqa: E402


def main() -> None:
    agent = Agent.from_directory("../plugins")
    runtime = agent.builder.build_runtime()
    server = AgentServer(runtime)
    server.run_http()


if __name__ == "__main__":
    main()
