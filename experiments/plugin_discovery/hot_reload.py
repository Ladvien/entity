from __future__ import annotations

import time
from typing import Callable, List

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .plugin_loader import LoadedPlugin, PluginLoader


class ReloadHandler(FileSystemEventHandler):
    def __init__(
        self, loader: PluginLoader, callback: Callable[[List[LoadedPlugin]], None]
    ) -> None:
        super().__init__()
        self.loader = loader
        self.callback = callback

    def on_any_event(self, event) -> None:  # noqa: D401 - intentionally simple
        if event.is_directory:
            return
        self.callback(self.loader.scan())


class HotReloader:
    """Monitor a directory and reload plugins when files change."""

    def __init__(
        self, directory: str, callback: Callable[[List[LoadedPlugin]], None]
    ) -> None:
        self.loader = PluginLoader(directory)
        self.callback = callback
        self._observer = Observer()
        self._handler = ReloadHandler(self.loader, self.callback)

    def start(self) -> None:
        self.callback(self.loader.scan())
        self._observer.schedule(
            self._handler, str(self.loader.directory), recursive=False
        )
        self._observer.start()

    def stop(self) -> None:
        self._observer.stop()
        self._observer.join()

    def __enter__(self) -> "HotReloader":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()


if __name__ == "__main__":

    def report(plugins: List[LoadedPlugin]) -> None:
        names = ", ".join(p.name for p in plugins)
        print(f"Loaded plugins: {names}")

    directory = "user_plugins"
    print(f"Watching {directory} for changes...")
    with HotReloader(directory, report):
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
