from __future__ import annotations

"""Memory resource interface wrapper."""


def __getattr__(name: str):
    if name == "Memory":
        from plugins.builtin.resources.memory import Memory

        return Memory
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["Memory"]
