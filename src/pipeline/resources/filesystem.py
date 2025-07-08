from __future__ import annotations

"""Pipeline component: filesystem."""

from typing import TYPE_CHECKING

"""Filesystem resource wrapper used by pipeline components."""

# Lazy import keeps optional filesystem drivers lightweight.

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from plugins.builtin.resources.filesystem import FileSystemResource


def __getattr__(name: str):
    if name == "FileSystemResource":
        from plugins.builtin.resources.filesystem import FileSystemResource

        return FileSystemResource
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["FileSystemResource"]
