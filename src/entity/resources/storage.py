"""Layer 3 canonical storage resource."""

from __future__ import annotations

from .interfaces import ResourceInitializationError, StorageResource


class Storage:
    """Unified interface for file and object storage."""

    def __init__(self, storage_resource: StorageResource) -> None:
        if storage_resource is None:
            raise ResourceInitializationError("StorageResource required")
        self.storage_resource = storage_resource

    async def setup(self) -> None:  # pragma: no cover - placeholder
        """Ensure storage backend is ready."""
        pass
