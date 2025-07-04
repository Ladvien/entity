from __future__ import annotations

"""Persistent queue implementation for retrying operations."""

import json
import os
from typing import Any, List


class PersistentQueue:
    """Simple file-backed FIFO queue."""

    def __init__(self, path: str) -> None:
        self._path = path
        self._queue: List[Any] = []
        self._load()

    def _load(self) -> None:
        if os.path.exists(self._path):
            with open(self._path, "r", encoding="utf-8") as fh:
                try:
                    self._queue = json.load(fh)
                except Exception:
                    self._queue = []
        else:
            self._queue = []

    def _save(self) -> None:
        with open(self._path, "w", encoding="utf-8") as fh:
            json.dump(self._queue, fh)

    def put(self, item: Any) -> None:
        self._queue.append(item)
        self._save()

    def get(self) -> Any | None:
        if not self._queue:
            return None
        item = self._queue.pop(0)
        self._save()
        return item

    def peek(self) -> Any | None:
        return self._queue[0] if self._queue else None

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._queue)
