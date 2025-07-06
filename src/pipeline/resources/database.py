from __future__ import annotations

from typing import TYPE_CHECKING

"""Database resource wrapper used by tests."""

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from plugins.builtin.resources.database import DatabaseResource


def __getattr__(name: str):
    if name == "DatabaseResource":
        from plugins.builtin.resources.database import DatabaseResource

        return DatabaseResource
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["DatabaseResource"]
