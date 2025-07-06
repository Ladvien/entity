from __future__ import annotations

"""Wrapper for SQLiteStorageResource."""


def __getattr__(name: str):
    if name == "SQLiteStorageResource":
        from plugins.builtin.resources.sqlite_storage import SQLiteStorageResource

        return SQLiteStorageResource
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["SQLiteStorageResource"]
