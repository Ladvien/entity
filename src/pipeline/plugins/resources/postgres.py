from __future__ import annotations

from typing import Any, Dict, List

import asyncpg
from asyncpg.utils import _quote_ident

from pipeline.plugins import ResourcePlugin
from pipeline.stages import PipelineStage

from .postgres_pool import PostgresConnectionPool


class PostgresResource(ResourcePlugin):
    """Thin wrapper around an asyncpg connection pool."""

    stages = [PipelineStage.PARSE]
    name = "database"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self._pool = PostgresConnectionPool(self.config)

    def _qualified_history_table(self) -> str:
        table = _quote_ident(self._history_table)
        if self._schema:
            schema = _quote_ident(self._schema)
            return f"{schema}.{table}"
        return table

    async def initialize(self) -> None:
<<<<< codex/implement-postgresconnectionpool-and-refactor-postgresresour
        await self._pool.initialize()
=====
        self.logger.info("Connecting to Postgres", extra={"config": self.config})
        self._connection = await asyncpg.connect(
            database=str(self.config.get("name")),
            host=str(self.config.get("host", "localhost")),
            port=int(self.config.get("port", 5432)),
            user=str(self.config.get("username")),
            password=str(self.config.get("password")),
        )
        if self._history_table:
            table = self._qualified_history_table()
            query = f"""
                CREATE TABLE IF NOT EXISTS {table} (
                    conversation_id TEXT,
                    role TEXT,
                    content TEXT,
                    metadata JSONB,
                    timestamp TIMESTAMPTZ
                )
            """
            await self._connection.execute(query)
>>>>> main

    async def _execute_impl(self, context) -> Any:  # pragma: no cover - no op
        return None

    async def health_check(self) -> bool:
        return await self._pool.health_check()

<<<< codex/implement-postgresconnectionpool-and-refactor-postgresresour
    async def execute(self, query: str, *args: Any) -> None:
        async with self._pool.connection() as conn:
            await conn.execute(query, *args)
=====
        table = self._qualified_history_table()
        for entry in history:
            query = (
                f"INSERT INTO {table} "
                "(conversation_id, role, content, metadata, timestamp)"
                " VALUES ($1, $2, $3, $4, $5)"
            )
            await self._connection.execute(
                query,
                conversation_id,
                entry.role,
                entry.content,
                json.dumps(entry.metadata),
                entry.timestamp,
            )
>>>>>> main

    async def fetch(self, query: str, *args: Any) -> List[asyncpg.Record]:
        async with self._pool.connection() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args: Any) -> asyncpg.Record | None:
        async with self._pool.connection() as conn:
            return await conn.fetchrow(query, *args)

<<<<<< codex/implement-postgresconnectionpool-and-refactor-postgresresour
    async def fetchval(self, query: str, *args: Any) -> Any:
        async with self._pool.connection() as conn:
            return await conn.fetchval(query, *args)
======
        table = self._qualified_history_table()
        query = (
            f"SELECT role, content, metadata, timestamp FROM {table} "
            "WHERE conversation_id=$1 ORDER BY timestamp"
        )
        rows = await self._connection.fetch(query, conversation_id)
        history: List[ConversationEntry] = []
        for row in rows:
            metadata = row["metadata"]
            if not isinstance(metadata, dict):
                metadata = json.loads(metadata) if metadata else {}
            history.append(
                ConversationEntry(
                    content=row["content"],
                    role=row["role"],
                    timestamp=row["timestamp"],
                    metadata=metadata,
                )
            )
        return history
>>>>>> main
