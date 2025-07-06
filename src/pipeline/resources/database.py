from __future__ import annotations

"""Database resource wrapper used by tests."""


def __getattr__(name: str):
    if name == "DatabaseResource":
        from plugins.builtin.resources.database import DatabaseResource

        return DatabaseResource
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["DatabaseResource"]
