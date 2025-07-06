import importlib
import inspect
import pkgutil

from pipeline.base_plugins import BasePlugin, ToolPlugin
from pipeline.stages import PipelineStage

PACKAGE_NAMES = [
    "user_plugins",
    "pipeline.resources",
]


def iter_modules(package_name: str):
    package = importlib.import_module(package_name)
    if getattr(package, "__path__", None) is None:
        return []
    return [
        m.name for m in pkgutil.walk_packages(package.__path__, package.__name__ + ".")
    ]


def gather_plugin_classes():
    classes = []
    for package_name in PACKAGE_NAMES:
        for module_name in iter_modules(package_name):
            try:
                module = importlib.import_module(module_name)
            except Exception:
                continue
            for obj in module.__dict__.values():
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, BasePlugin)
                    and obj not in {BasePlugin, ToolPlugin}
                    and obj.__module__ == module.__name__
                ):
                    classes.append(obj)
    return classes


def test_plugins_define_valid_stages():
    for plugin_cls in gather_plugin_classes():
        if issubclass(plugin_cls, ToolPlugin):
            continue
        stages = getattr(plugin_cls, "stages", None)
        assert stages, f"{plugin_cls.__name__} missing stages"
        assert all(
            isinstance(stage, PipelineStage) for stage in stages
        ), f"{plugin_cls.__name__} has invalid stage"
