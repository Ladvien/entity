"""Resource for storing text to an S3 bucket."""

from entity.infrastructure.protocols import StorageInfrastructure
from entity.resources.exceptions import ResourceInitializationError


class StorageResource:
    """Layer 2 resource for S3-based file storage."""

    def __init__(self, infrastructure: StorageInfrastructure | None) -> None:
        """Initialize the resource with a storage infrastructure instance."""

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
        """Upload plain text to the configured storage under the given key."""

        await self.infrastructure.write(key, data.encode("utf-8"))
