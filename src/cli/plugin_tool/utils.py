from __future__ import annotations

import importlib.util
import inspect
from pathlib import Path
from typing import Type

from entity.core.plugins import BasePlugin


def load_plugin(path: str) -> Type[BasePlugin]:
    mod_path = Path(path)
    module_name = mod_path.stem
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for obj in module.__dict__.values():
        if (
            inspect.isclass(obj)
            and issubclass(obj, BasePlugin)
            and obj is not BasePlugin
        ):
            return obj
    raise RuntimeError("No plugin class found")


__all__ = ["load_plugin"]
