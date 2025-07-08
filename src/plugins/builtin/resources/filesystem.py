from __future__ import annotations

"""Built-in plugins and resources."""

from abc import ABC, abstractmethod


class FileSystemResource(ABC):
    """Abstract interface for filesystem-like storage backends."""

    @abstractmethod
    async def store(self, key: str, content: bytes) -> str:
        """Persist ``content`` under ``key`` and return storage path."""

    @abstractmethod
    async def load(self, key: str) -> bytes:
        """Retrieve previously stored bytes for ``key``."""
