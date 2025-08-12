from __future__ import annotations

import asyncio

from entity.infrastructure.protocols import StorageInfrastructure
from entity.resources.exceptions import ResourceInitializationError


class LocalStorageResource:
    """Layer 2 resource for local file storage."""

    def __init__(self, infrastructure: StorageInfrastructure | None) -> None:
        """Create the resource with a storage backend."""

        if infrastructure is None:
            raise ResourceInitializationError("StorageInfrastructure is required")
        self.infrastructure = infrastructure

    async def health_check(self) -> bool:
        """Return ``True`` if the underlying infrastructure is healthy."""

        return await self.infrastructure.health_check()

    def health_check_sync(self) -> bool:
        """Synchronous wrapper for health_check for compatibility."""
        return self.infrastructure.health_check_sync()

    async def upload_text(self, key: str, data: str) -> None:
        """Persist text to the local filesystem."""

        if hasattr(self.infrastructure, "resolve_path"):
            path = self.infrastructure.resolve_path(key)
            path.parent.mkdir(parents=True, exist_ok=True)
            await asyncio.to_thread(path.write_text, data)
        else:
            await self.infrastructure.write(key, data.encode("utf-8"))
