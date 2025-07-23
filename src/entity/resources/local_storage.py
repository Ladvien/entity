from __future__ import annotations

import asyncio
from pathlib import Path

from entity.infrastructure.local_storage_infra import LocalStorageInfrastructure


class LocalStorageResource:
    """Layer 2 resource for local file storage."""

    def __init__(self, infrastructure: LocalStorageInfrastructure) -> None:
        """Create the resource with a local storage backend."""

        self.infrastructure = infrastructure

    async def upload_text(self, key: str, data: str) -> None:
        """Persist text to the local filesystem."""

        path = self.infrastructure.resolve_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(path.write_text, data)
