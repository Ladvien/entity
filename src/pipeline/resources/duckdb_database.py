from __future__ import annotations

"""Pipeline component: duckdb database."""

from typing import TYPE_CHECKING

"""Wrapper for DuckDBDatabaseResource."""

# Defer duckdb import until the resource is accessed.

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from plugins.builtin.resources.duckdb_database import DuckDBDatabaseResource


def __getattr__(name: str):
    if name == "DuckDBDatabaseResource":
        from plugins.builtin.resources.duckdb_database import DuckDBDatabaseResource

        return DuckDBDatabaseResource
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["DuckDBDatabaseResource"]
