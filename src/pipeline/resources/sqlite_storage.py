from __future__ import annotations

"""Pipeline component: sqlite storage."""

from typing import TYPE_CHECKING

"""Wrapper for SQLiteStorageResource."""

# Lazy import avoids pulling in SQLite driver during startup.

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from plugins.builtin.resources.sqlite_storage import SQLiteStorageResource


def __getattr__(name: str):
    if name == "SQLiteStorageResource":
        from plugins.builtin.resources.sqlite_storage import SQLiteStorageResource

        return SQLiteStorageResource
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["SQLiteStorageResource"]
