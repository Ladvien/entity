from __future__ import annotations

import asyncio

from entity.infrastructure.local_storage_infra import LocalStorageInfrastructure
from entity.resources.exceptions import ResourceInitializationError


class LocalStorageResource:
    """Layer 2 resource for local file storage."""

    def __init__(self, infrastructure: LocalStorageInfrastructure | None) -> None:
        """Create the resource with a local storage backend."""

        if infrastructure is None:
            raise ResourceInitializationError("LocalStorageInfrastructure is required")
        self.infrastructure = infrastructure

    def health_check(self) -> bool:
        """Return ``True`` if the underlying infrastructure is healthy."""

        return self.infrastructure.health_check()

    async def upload_text(self, key: str, data: str) -> None:
        """Persist text to the local filesystem."""

        path = self.infrastructure.resolve_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(path.write_text, data)
