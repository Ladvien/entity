from __future__ import annotations

"""Wrapper for InMemoryStorageResource."""


def __getattr__(name: str):
    if name == "InMemoryStorageResource":
        from plugins.builtin.resources.in_memory_storage import InMemoryStorageResource

        return InMemoryStorageResource
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["InMemoryStorageResource"]
