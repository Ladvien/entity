"""Protocol definitions for infrastructure interfaces."""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class DatabaseInfrastructure(Protocol):
    """Protocol for database infrastructure implementations."""

    async def startup(self) -> None:
        """Perform asynchronous initialization."""
        ...

    async def shutdown(self) -> None:
        """Perform asynchronous cleanup."""
        ...

    async def health_check(self) -> bool:
        """Return True if the infrastructure is healthy."""
        ...

    def connect(self) -> Any:
        """Return a database connection context manager."""
        ...


@runtime_checkable
class VectorStoreInfrastructure(Protocol):
    """Protocol for vector store infrastructure implementations."""

    async def startup(self) -> None:
        """Perform asynchronous initialization."""
        ...

    async def shutdown(self) -> None:
        """Perform asynchronous cleanup."""
        ...

    async def health_check(self) -> bool:
        """Return True if the infrastructure is healthy."""
        ...

    def connect(self) -> Any:
        """Return a vector store connection context manager."""
        ...


@runtime_checkable
class StorageInfrastructure(Protocol):
    """Protocol for storage infrastructure implementations."""

    async def startup(self) -> None:
        """Perform asynchronous initialization."""
        ...

    async def shutdown(self) -> None:
        """Perform asynchronous cleanup."""
        ...

    async def health_check(self) -> bool:
        """Return True if the infrastructure is healthy."""
        ...

    def resolve(self, path: str) -> str:
        """Resolve a path relative to the storage root."""
        ...

    async def read(self, path: str) -> bytes:
        """Read file contents."""
        ...

    async def write(self, path: str, data: bytes) -> None:
        """Write file contents."""
        ...

    async def delete(self, path: str) -> None:
        """Delete a file."""
        ...

    async def exists(self, path: str) -> bool:
        """Check if a file exists."""
        ...

    async def list_files(self, prefix: str = "") -> list[str]:
        """List files with optional prefix."""
        ...
