from entity.resources.storage import StorageResource
from entity.resources.local_storage import LocalStorageResource
from entity.resources.exceptions import ResourceInitializationError


class FileStorage:
    """Layer 3 wrapper around a storage resource."""

    def __init__(self, resource: StorageResource | LocalStorageResource | None) -> None:
        """Wrap a local or S3 storage resource."""

        if resource is None:
            raise ResourceInitializationError("StorageResource is required")
        self.resource = resource

    def health_check(self) -> bool:
        """Return ``True`` if the underlying resource is healthy."""

        return self.resource.health_check()

    async def upload_text(self, key: str, data: str) -> None:
        """Proxy text upload to the underlying resource."""

        await self.resource.upload_text(key, data)
