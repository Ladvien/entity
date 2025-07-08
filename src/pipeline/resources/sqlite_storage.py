from __future__ import annotations

from typing import TYPE_CHECKING

"""Wrapper for SQLiteStorageResource."""

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from plugins.builtin.resources.sqlite_storage import SQLiteStorageResource


def __getattr__(name: str):
    if name == "SQLiteStorageResource":
        from plugins.builtin.resources.sqlite_storage import SQLiteStorageResource

        return SQLiteStorageResource
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["SQLiteStorageResource"]
