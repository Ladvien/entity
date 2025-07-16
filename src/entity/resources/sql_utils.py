# Utility helpers for executing SQL queries across resources
from __future__ import annotations

from typing import Any
import inspect


class _RowCursor:
    """Lightweight wrapper mimicking a DB-API cursor."""

    def __init__(self, rows: list[Any]) -> None:
        self._rows = [tuple(r) for r in rows]
        self._index = 0
        if rows and hasattr(rows[0], "keys"):
            keys = list(rows[0].keys())
        else:
            keys = [str(i) for i in range(len(self._rows[0]))] if rows else []
        self.description = [(k, None, None, None, None, None, None) for k in keys]

    def fetchall(self) -> list[Any]:
        return self._rows

    def fetchone(self) -> Any:
        if self._index >= len(self._rows):
            return None
        row = self._rows[self._index]
        self._index += 1
        return row


def _detect_paramstyle(conn: Any) -> str:
    """Return the DB-API paramstyle for ``conn`` or a safe default."""
    style = getattr(conn, "paramstyle", None)
    if style:
        return style
    module = inspect.getmodule(conn)
    module_name = getattr(module, "__name__", "") if module else ""
    if module_name.startswith("asyncpg") or hasattr(conn, "fetchval"):
        return "numeric"
    return getattr(module, "paramstyle", "qmark")


def _convert_placeholders(sql: str, style: str) -> str:
    """Convert ``?`` placeholders in ``sql`` to match ``style``."""
    if style in {"format", "pyformat"}:
        return sql.replace("?", "%s")
    if style == "numeric":
        parts = sql.split("?")
        if len(parts) == 1:
            return sql
        new = []
        for index, part in enumerate(parts[:-1], start=1):
            new.append(part)
            new.append(f"${index}")
        new.append(parts[-1])
        return "".join(new)
    return sql


async def _execute(conn: Any, sql: str, params: Any | None = None) -> Any:
    """Run a query against ``conn`` and await the result when necessary."""
    style = _detect_paramstyle(conn)
    sql = _convert_placeholders(sql, style)

    asyncpg_like = hasattr(conn, "fetch")
    is_select = sql.lstrip().lower().startswith(("select", "with"))

    if asyncpg_like and is_select:
        rows = conn.fetch(sql, *params) if params else conn.fetch(sql)
        if inspect.isawaitable(rows):
            rows = await rows
        return _RowCursor(list(rows))

    if not params:
        result = conn.execute(sql)
    else:
        try:
            result = conn.execute(sql, *params)
        except Exception:
            result = conn.execute(sql, params)
    if inspect.isawaitable(result):
        result = await result
    return result


async def _maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value
