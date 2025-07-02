from __future__ import annotations

import asyncio
import pathlib
from typing import Dict

from pipeline.plugins import ResourcePlugin
from pipeline.resources.filesystem import FileSystemResource
from pipeline.stages import PipelineStage


class LocalFileSystemResource(ResourcePlugin, FileSystemResource):
    """Persist files on the local disk."""

    stages = [PipelineStage.PARSE]
    name = "filesystem"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        base_path = self.config.get("base_path", "./data")
        self._base = pathlib.Path(base_path)

    async def _execute_impl(self, context) -> None:  # pragma: no cover - no op
        return None

    async def store(self, key: str, content: bytes) -> str:
        path = self._base / key
        path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(path.write_bytes, content)
        return str(path)

    async def load(self, key: str) -> bytes:
        path = self._base / key
        return await asyncio.to_thread(path.read_bytes)
