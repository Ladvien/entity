from __future__ import annotations

"""Filesystem resource wrapper used by pipeline components."""


def __getattr__(name: str):
    if name == "FileSystemResource":
        from plugins.builtin.resources.filesystem import FileSystemResource

        return FileSystemResource
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["FileSystemResource"]
