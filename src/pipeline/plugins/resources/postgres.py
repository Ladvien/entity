from __future__ import annotations

from typing import Any, Dict, Optional

import asyncpg

from pipeline.plugins import ResourcePlugin
from pipeline.stages import PipelineStage


class PostgresResource(ResourcePlugin):
    """Asynchronous PostgreSQL connection resource."""

    stages = [PipelineStage.PARSE]
    name = "database"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self._connection: Optional[asyncpg.Connection] = None

    async def initialize(self) -> None:
        self._connection = await asyncpg.connect(
            database=str(self.config.get("name")),
            host=str(self.config.get("host", "localhost")),
            port=int(self.config.get("port", 5432)),
            user=str(self.config.get("username")),
            password=str(self.config.get("password")),
        )

    async def _execute_impl(self, context) -> Any:  # pragma: no cover - no op
        return None

    async def health_check(self) -> bool:
        if self._connection is None:
            return False
        try:
            await self._connection.fetchval("SELECT 1")
            return True
        except Exception:
            return False
