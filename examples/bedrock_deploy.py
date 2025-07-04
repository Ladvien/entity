"""Auto deploy AWS Bedrock infrastructure."""

from __future__ import annotations

import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))


def _enable_plugins_namespace() -> None:
    import importlib
    import pkgutil
    import types

    plugins_mod = types.ModuleType("plugins")
    plugins_mod.__path__ = [
        str(pathlib.Path(__file__).resolve().parents[1] / "plugins")
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

from infrastructure.aws_bedrock import deploy

if __name__ == "__main__":  # pragma: no cover - manual example
    try:
        deploy()
    except FileNotFoundError as exc:
        print(f"cdktf not available: {exc}")
