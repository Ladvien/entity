from __future__ import annotations

"""Public re-export of :class:`LLM`."""


def __getattr__(name: str):
    if name == "LLM":
        from plugins.builtin.resources.llm_base import LLM

        return LLM
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["LLM"]
