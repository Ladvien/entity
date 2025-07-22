from .storage import StorageResource
from .local_storage import LocalStorageResource
from .exceptions import ResourceInitializationError


class Storage:
    """Layer 3 wrapper around a storage resource."""

    def __init__(self, resource: StorageResource | LocalStorageResource | None) -> None:
        if resource is None:
            raise ResourceInitializationError("StorageResource is required")
        self.resource = resource

    async def upload_text(self, key: str, data: str) -> None:
        await self.resource.upload_text(key, data)
