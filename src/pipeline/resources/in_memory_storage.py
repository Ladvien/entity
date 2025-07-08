from __future__ import annotations

"""Pipeline component: in memory storage."""

from typing import TYPE_CHECKING

"""Wrapper for InMemoryStorageResource."""

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from plugins.builtin.resources.in_memory_storage import InMemoryStorageResource


def __getattr__(name: str):
    if name == "InMemoryStorageResource":
        from plugins.builtin.resources.in_memory_storage import InMemoryStorageResource

        return InMemoryStorageResource
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["InMemoryStorageResource"]
