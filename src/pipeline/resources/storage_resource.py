from __future__ import annotations

from typing import TYPE_CHECKING

"""Thin wrapper exposing the built-in filesystem StorageResource."""

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from plugins.builtin.resources.storage_resource import StorageResource


def __getattr__(name: str):
    if name == "StorageResource":
        from plugins.builtin.resources.storage_resource import StorageResource

        return StorageResource
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["StorageResource"]
