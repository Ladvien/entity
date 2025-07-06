from __future__ import annotations

"""Wrapper for DuckDBDatabaseResource."""


def __getattr__(name: str):
    if name == "DuckDBDatabaseResource":
        from plugins.builtin.resources.duckdb_database import DuckDBDatabaseResource

        return DuckDBDatabaseResource
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["DuckDBDatabaseResource"]
