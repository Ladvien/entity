from __future__ import annotations

from typing import TYPE_CHECKING

"""Memory resource interface wrapper."""

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from plugins.builtin.resources.memory import Memory


def __getattr__(name: str):
    if name == "Memory":
        from plugins.builtin.resources.memory import Memory

        return Memory
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["Memory"]
