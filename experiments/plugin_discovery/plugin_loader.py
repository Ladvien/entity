from __future__ import annotations

"""Simple plugin loader used for experimentation only."""

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import List, Dict, Type

from pipeline.base_plugins import BasePlugin
from pipeline.utils import DependencyGraph


@dataclass
class LoadedPlugin:
    """Simple container for discovered plugin classes."""

    name: str
    cls: Type[BasePlugin]
    module: ModuleType
    dependencies: List[str]


class PluginLoader:
    """Load plugins from a directory and order them by dependencies."""

    def __init__(self, directory: str) -> None:
        self.directory = Path(directory)

    def _import_module(self, file: Path) -> ModuleType | None:
        spec = importlib.util.spec_from_file_location(file.stem, file)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        return None

    def scan(self) -> List[LoadedPlugin]:
        plugins: List[LoadedPlugin] = []
        for file in self.directory.glob("*.py"):
            if file.name.startswith("_"):
                continue
            module = self._import_module(file)
            if not module:
                continue
            for obj in vars(module).values():
                if (
                    isinstance(obj, type)
                    and issubclass(obj, BasePlugin)
                    and obj is not BasePlugin
                ):
                    name = getattr(obj, "name", obj.__name__)
                    deps = list(getattr(obj, "dependencies", []))
                    plugins.append(LoadedPlugin(name, obj, module, deps))
        return self._sort_by_dependencies(plugins)

    def _sort_by_dependencies(self, plugins: List[LoadedPlugin]) -> List[LoadedPlugin]:
        graph: Dict[str, List[str]] = {p.name: p.dependencies for p in plugins}
        order = DependencyGraph(graph).topological_sort()
        name_map = {p.name: p for p in plugins}
        return [name_map[n] for n in order if n in name_map]
