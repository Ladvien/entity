from __future__ import annotations

"""Helpers for discovering workflow classes."""

from importlib import util
from pathlib import Path
from types import ModuleType
from typing import Dict, Type
import inspect

from entity.utils.logging import get_logger

from . import Workflow

__all__ = ["discover_workflows", "register_module_workflows"]

logger = get_logger(__name__)


def _import_module(file: Path) -> ModuleType | None:
    try:
        spec = util.spec_from_file_location(file.stem, file)
        if spec and spec.loader:
            module = util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to import workflow module %s: %s", file, exc)
    return None


def register_module_workflows(
    module: ModuleType, registry: Dict[str, Type[Workflow]]
) -> None:
    for name, obj in vars(module).items():
        if name.startswith("_"):
            continue
        if inspect.isclass(obj) and issubclass(obj, Workflow) and obj is not Workflow:
            registry[obj.__name__] = obj


def discover_workflows(directory: str) -> Dict[str, Type[Workflow]]:
    """Load ``*.py`` files from ``directory`` and collect ``Workflow`` subclasses."""

    registry: Dict[str, Type[Workflow]] = {}
    for file in Path(directory).glob("*.py"):
        if file.name.startswith("_"):
            continue
        module = _import_module(file)
        if module is not None:
            register_module_workflows(module, registry)
    return registry
