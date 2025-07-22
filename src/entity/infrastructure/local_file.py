from __future__ import annotations


class LocalFileInfrastructure:
    """Infrastructure primitive for file storage on the local filesystem."""

    def __init__(self, base_path: str) -> None:
        self.base_path = base_path

    async def setup(self) -> None:  # pragma: no cover - placeholder
        """Prepare the base directory."""
        pass
