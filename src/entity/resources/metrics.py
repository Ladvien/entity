from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager
import json
import time

from entity.core.stages import PipelineStage
from .sql_utils import _execute, _maybe_await


@dataclass
class PluginExecutionRecord:
    pipeline_id: str
    stage: PipelineStage | None
    plugin_name: str
    duration_ms: float
    success: bool
    error_type: Optional[str] = None


@dataclass
class ResourceOperationRecord:
    pipeline_id: str
    resource_name: str
    operation: str
    duration_ms: float
    success: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CustomMetricRecord:
    pipeline_id: str
    metric_name: str
    value: float
    metadata: Dict[str, Any] = field(default_factory=dict)


from .base import AgentResource
from .database import DatabaseResource
import aiosqlite


class MetricsCollectorResource(AgentResource):
    """Persist plugin and resource metrics to a database."""

    name = "metrics_collector"
    resource_category = "observability"
    dependencies = ["database?"]
    infrastructure_dependencies: list[str] = []

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        super().__init__(config or {})
        self.database: DatabaseResource | None = None
        self._conn: Any | None = None
        self.counters: Dict[str, int] = {}

    async def initialize(self) -> None:
        if self.database is None:
            self._conn = await aiosqlite.connect(":memory:")
            await self._create_tables(self._conn)
            await self._clear_tables(self._conn)
        else:
            async with self.database.connection() as conn:
                await self._create_tables(conn)
                await self._clear_tables(conn)

    async def shutdown(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    async def _execute_impl(self, context: Any) -> None:  # pragma: no cover - stub
        return None

    async def _create_tables(self, conn: Any) -> None:
        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS plugin_metrics (
                pipeline_id TEXT,
                stage TEXT,
                plugin_name TEXT,
                duration_ms REAL,
                success INTEGER,
                error_type TEXT
            )
            """,
        )
        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS resource_metrics (
                pipeline_id TEXT,
                resource_name TEXT,
                operation TEXT,
                duration_ms REAL,
                success INTEGER,
                metadata TEXT
            )
            """,
        )
        await _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS custom_metrics (
                pipeline_id TEXT,
                metric_name TEXT,
                value REAL,
                metadata TEXT
            )
            """,
        )

    async def _clear_tables(self, conn: Any) -> None:
        await _execute(conn, "DELETE FROM plugin_metrics")
        await _execute(conn, "DELETE FROM resource_metrics")
        await _execute(conn, "DELETE FROM custom_metrics")

    # ------------------------------------------------------------------
    # Recording methods
    # ------------------------------------------------------------------
    async def record_plugin_execution(
        self,
        *,
        pipeline_id: str,
        stage: PipelineStage | None,
        plugin_name: str,
        duration_ms: float,
        success: bool,
        error_type: str | None = None,
    ) -> None:
        await self._execute(
            "INSERT INTO plugin_metrics VALUES (?, ?, ?, ?, ?, ?)",
            (
                pipeline_id,
                stage.name if stage else None,
                plugin_name,
                duration_ms,
                int(success),
                error_type,
            ),
        )

    async def record_resource_operation(
        self,
        *,
        pipeline_id: str,
        resource_name: str,
        operation: str,
        duration_ms: float,
        success: bool,
        metadata: Dict[str, Any] | None = None,
    ) -> None:
        await self._execute(
            "INSERT INTO resource_metrics VALUES (?, ?, ?, ?, ?, ?)",
            (
                pipeline_id,
                resource_name,
                operation,
                duration_ms,
                int(success),
                json.dumps(metadata or {}),
            ),
        )

    async def record_custom_metric(
        self,
        *,
        pipeline_id: str,
        metric_name: str,
        value: float,
        metadata: Dict[str, Any] | None = None,
    ) -> None:
        await self._execute(
            "INSERT INTO custom_metrics VALUES (?, ?, ?, ?)",
            (
                pipeline_id,
                metric_name,
                value,
                json.dumps(metadata or {}),
            ),
        )

    async def increment_counter(
        self,
        *,
        pipeline_id: str,
        counter_name: str,
        increment: int = 1,
        metadata: Dict[str, Any] | None = None,
    ) -> None:
        key = f"{pipeline_id}:{counter_name}"
        self.counters[key] = self.counters.get(key, 0) + increment
        if metadata is not None:
            # store metadata as custom metric for traceability
            await self.record_custom_metric(
                pipeline_id=pipeline_id,
                metric_name=f"counter:{counter_name}",
                value=self.counters[key],
                metadata=metadata,
            )

    # ------------------------------------------------------------------
    # Retrieval methods
    # ------------------------------------------------------------------
    async def get_plugin_executions(
        self, pipeline_id: str | None = None
    ) -> List[PluginExecutionRecord]:
        sql = "SELECT pipeline_id, stage, plugin_name, duration_ms, success, error_type FROM plugin_metrics"
        params: List[Any] = []
        if pipeline_id:
            sql += " WHERE pipeline_id = ?"
            params.append(pipeline_id)
        rows = await self._query(sql, params)
        return [
            PluginExecutionRecord(
                pipeline_id=row[0],
                stage=PipelineStage[row[1]] if row[1] else None,
                plugin_name=row[2],
                duration_ms=row[3],
                success=bool(row[4]),
                error_type=row[5],
            )
            for row in rows
        ]

    async def get_resource_operations(
        self, pipeline_id: str | None = None
    ) -> List[ResourceOperationRecord]:
        sql = "SELECT pipeline_id, resource_name, operation, duration_ms, success, metadata FROM resource_metrics"
        params: List[Any] = []
        if pipeline_id:
            sql += " WHERE pipeline_id = ?"
            params.append(pipeline_id)
        rows = await self._query(sql, params)
        return [
            ResourceOperationRecord(
                pipeline_id=row[0],
                resource_name=row[1],
                operation=row[2],
                duration_ms=row[3],
                success=bool(row[4]),
                metadata=json.loads(row[5]) if row[5] else {},
            )
            for row in rows
        ]

    async def get_custom_metrics(
        self,
        pipeline_id: str | None = None,
        metric_name: str | None = None,
    ) -> List[CustomMetricRecord]:
        sql = "SELECT pipeline_id, metric_name, value, metadata FROM custom_metrics"
        params: List[Any] = []
        clauses: List[str] = []
        if pipeline_id:
            clauses.append("pipeline_id = ?")
            params.append(pipeline_id)
        if metric_name:
            clauses.append("metric_name = ?")
            params.append(metric_name)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        rows = await self._query(sql, params)
        return [
            CustomMetricRecord(
                pipeline_id=row[0],
                metric_name=row[1],
                value=row[2],
                metadata=json.loads(row[3]) if row[3] else {},
            )
            for row in rows
        ]

    # ------------------------------------------------------------------
    # Context managers
    # ------------------------------------------------------------------
    @asynccontextmanager
    async def track_plugin_execution(
        self,
        *,
        pipeline_id: str,
        stage: PipelineStage | None,
        plugin_name: str,
    ) -> Any:
        start = time.perf_counter()
        success = True
        error_type: str | None = None
        try:
            yield
        except Exception as exc:
            success = False
            error_type = exc.__class__.__name__
            raise
        finally:
            duration = (time.perf_counter() - start) * 1000
            await self.record_plugin_execution(
                pipeline_id=pipeline_id,
                stage=stage,
                plugin_name=plugin_name,
                duration_ms=duration,
                success=success,
                error_type=error_type,
            )

    @asynccontextmanager
    async def track_resource_operation(
        self,
        *,
        pipeline_id: str,
        resource_name: str,
        operation: str,
        metadata: Dict[str, Any] | None = None,
    ) -> Any:
        start = time.perf_counter()
        success = True
        try:
            yield
        except Exception:
            success = False
            raise
        finally:
            duration = (time.perf_counter() - start) * 1000
            await self.record_resource_operation(
                pipeline_id=pipeline_id,
                resource_name=resource_name,
                operation=operation,
                duration_ms=duration,
                success=success,
                metadata=metadata,
            )

    async def _execute(
        self, sql: str, params: List[Any] | tuple[Any, ...] | None = None
    ) -> None:
        conn = self._conn
        if conn is not None:
            await _execute(conn, sql, params)
            return
        if self.database is None:
            raise RuntimeError("Metrics collector not initialized")
        async with self.database.connection() as db_conn:
            await _execute(db_conn, sql, params)

    async def _query(self, sql: str, params: List[Any] | None = None) -> List[Any]:
        conn = self._conn
        if conn is not None:
            cursor = await _execute(conn, sql, params)
            return await _maybe_await(cursor.fetchall())
        if self.database is None:
            raise RuntimeError("Metrics collector not initialized")
        async with self.database.connection() as db_conn:
            cursor = await _execute(db_conn, sql, params)
            return await _maybe_await(cursor.fetchall())


__all__ = ["MetricsCollectorResource"]
