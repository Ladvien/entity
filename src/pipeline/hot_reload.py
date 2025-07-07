from __future__ import annotations

import asyncio
import importlib.util
from contextlib import suppress
from pathlib import Path
from types import ModuleType
from typing import Iterable, List

from watchfiles import awatch

from registry import PluginRegistry

from .base_plugins import BasePlugin
from .config_update import wait_for_pipeline_completion
from .manager import PipelineManager


class PluginReloader:
    """Watch plugin directories and hot reload changed modules."""

    def __init__(
        self,
        registry: PluginRegistry,
        directories: Iterable[str],
        *,
        pipeline_manager: PipelineManager | None = None,
    ) -> None:
        self.registry = registry
        self.pipeline_manager = pipeline_manager
        self.directories = [Path(d).resolve() for d in directories]
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._watch_loop())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task

    async def __aenter__(self) -> "PluginReloader":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.stop()

    async def _watch_loop(self) -> None:
        async for changes in awatch(*self.directories):
            await wait_for_pipeline_completion(self.pipeline_manager)
            for _change, path in changes:
                if path.endswith(".py"):
                    await self._reload_path(Path(path))

    async def _reload_path(self, path: Path) -> None:
        module = self._import_module(path)
        if module is None:
            return
        await self._reload_plugins_from_module(module)

    @staticmethod
    def _import_module(path: Path) -> ModuleType | None:
        spec = importlib.util.spec_from_file_location(path.stem, path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        return None

    async def _reload_plugins_from_module(self, module: ModuleType) -> None:
        for obj in vars(module).values():
            if (
                isinstance(obj, type)
                and issubclass(obj, BasePlugin)
                and obj is not BasePlugin
            ):
                name = getattr(obj, "name", obj.__name__)
                instance = self.registry.get_by_name(name)
                if instance is None:
                    continue
                config = getattr(instance, "config", {})
                try:
                    new_instance = obj(config)
                except Exception:
                    new_instance = obj()
                await self.registry.replace_plugin(name, new_instance)
