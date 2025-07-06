from __future__ import annotations

"""Simple filesystem backed storage resource."""

from typing import Dict

from pipeline.base_plugins import ResourcePlugin, ValidationResult

from .filesystem import FileSystemResource


class StorageResource(ResourcePlugin):
    """Provide simple file CRUD operations through a filesystem backend."""

    name = "storage"
    dependencies = ["filesystem"]

    def __init__(
        self,
        filesystem: FileSystemResource | None = None,
        config: Dict | None = None,
    ) -> None:
        super().__init__(config or {})
        self.filesystem = filesystem

    @classmethod
    def from_config(cls, config: Dict) -> "StorageResource":
        return cls(config=config)

    async def store_file(self, key: str, content: bytes) -> str:
        if not self.filesystem:
            raise ValueError("No filesystem backend configured")
        return await self.filesystem.store(key, content)

    async def load_file(self, key: str) -> bytes:
        if not self.filesystem:
            raise ValueError("No filesystem backend configured")
        return await self.filesystem.load(key)

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        for name in ("filesystem",):
            sub = config.get(name)
            if sub is not None and not isinstance(sub, dict):
                return ValidationResult.error_result(f"'{name}' must be a mapping")
        return ValidationResult.success_result()


__all__ = ["StorageResource"]
