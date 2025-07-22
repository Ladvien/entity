from __future__ import annotations


class DuckDBInfrastructure:
    """Infrastructure primitive for DuckDB storage."""

    def __init__(self, path: str) -> None:
        self.path = path

    async def setup(self) -> None:  # pragma: no cover - placeholder
        """Create the database file if needed."""
        pass
