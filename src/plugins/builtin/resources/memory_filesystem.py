from __future__ import annotations

"""In-memory file system resource."""

from typing import Dict

from plugins.builtin.resources.base import BaseResource
from plugins.builtin.resources.filesystem import FileSystemResource


class MemoryFileSystem(BaseResource, FileSystemResource):
    """Store files in an in-memory dictionary."""

    name = "filesystem"
    dependencies: list[str] = []

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self._files: Dict[str, bytes] = {}

    async def store(self, key: str, content: bytes) -> str:
        self._files[key] = content
        return key

    async def load(self, key: str) -> bytes:
        return self._files[key]
