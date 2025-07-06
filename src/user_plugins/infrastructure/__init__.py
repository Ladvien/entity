from importlib import import_module
from types import ModuleType


def __getattr__(name: str) -> ModuleType:
    return import_module(f"plugins.contrib.infrastructure.{name}")
