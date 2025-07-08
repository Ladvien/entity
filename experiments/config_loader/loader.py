from __future__ import annotations

"""Prototype config watcher for demos only, not production ready."""

import asyncio
from pathlib import Path
from typing import Any, Callable

from pipeline.config import ConfigLoader


class ConfigWatcher:
    """Load a config file and watch for changes."""

    def __init__(self, path: str | Path, env_file: str = ".env") -> None:
        self.path = Path(path)
        self.env_file = env_file
        self.config: dict[str, Any] = ConfigLoader.from_yaml(self.path, env_file)
        self._mtime = self.path.stat().st_mtime
        self._task: asyncio.Task[None] | None = None

    def start(
        self,
        callback: Callable[[dict[str, Any]], None] | None = None,
        interval: float = 1.0,
    ) -> None:
        """Begin watching ``path`` for modifications."""

        async def watch() -> None:
            while True:
                await asyncio.sleep(interval)
                mtime = self.path.stat().st_mtime
                if mtime != self._mtime:
                    self._mtime = mtime
                    self.config = ConfigLoader.from_yaml(self.path, self.env_file)
                    if callback:
                        callback(self.config)

        self._task = asyncio.create_task(watch())

    def stop(self) -> None:
        """Stop watching the file."""
        if self._task:
            self._task.cancel()
