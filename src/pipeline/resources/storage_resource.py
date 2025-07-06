from __future__ import annotations

"""Thin wrapper exposing the built-in filesystem StorageResource."""


def __getattr__(name: str):
    if name == "StorageResource":
        from plugins.builtin.resources.storage_resource import StorageResource

        return StorageResource
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["StorageResource"]
