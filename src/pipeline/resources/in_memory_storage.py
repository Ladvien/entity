from __future__ import annotations

from typing import TYPE_CHECKING

"""Wrapper for InMemoryStorageResource."""

# Import lazily so heavy plugin deps load only when accessed.

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from plugins.builtin.resources.in_memory_storage import InMemoryStorageResource


def __getattr__(name: str):
    if name == "InMemoryStorageResource":
        from plugins.builtin.resources.in_memory_storage import InMemoryStorageResource

        return InMemoryStorageResource
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["InMemoryStorageResource"]
