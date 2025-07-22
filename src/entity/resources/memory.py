"""Layer 3 canonical memory resource."""

from __future__ import annotations

from typing import Any

from .interfaces import DatabaseResource, ResourceInitializationError


class Memory:
    """Unified interface for persistent memory."""

    def __init__(self, database: DatabaseResource, config: dict | None = None) -> None:
        if database is None:
            raise ResourceInitializationError("DatabaseResource required")
        self.database = database
        self.config = config or {}

    async def setup(self) -> None:  # pragma: no cover - placeholder
        """Validate backing database."""
        pass
