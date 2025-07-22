"""Layer 2 resource interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ResourceInitializationError(Exception):
    """Raised when a resource is instantiated without required dependencies."""


class DatabaseResource(ABC):
    """Technology-agnostic database API."""

    def __init__(self, infrastructure: Any) -> None:
        if infrastructure is None:
            raise ResourceInitializationError("Infrastructure dependency required")
        self.infrastructure = infrastructure

    @abstractmethod
    async def query(self, *args: Any, **kwargs: Any) -> Any:
        """Execute a query against the underlying database."""


class LLMResource(ABC):
    """Technology-agnostic interface to a language model."""

    def __init__(self, infrastructure: Any) -> None:
        if infrastructure is None:
            raise ResourceInitializationError("Infrastructure dependency required")
        self.infrastructure = infrastructure

    @abstractmethod
    async def generate(self, prompt: str) -> Any:
        """Generate a response from the model."""


class StorageResource(ABC):
    """Technology-agnostic interface for file/object storage."""

    def __init__(self, infrastructure: Any) -> None:
        if infrastructure is None:
            raise ResourceInitializationError("Infrastructure dependency required")
        self.infrastructure = infrastructure

    @abstractmethod
    async def read(self, key: str) -> bytes:
        """Retrieve a stored object."""

    @abstractmethod
    async def write(self, key: str, data: bytes) -> None:
        """Persist an object."""
