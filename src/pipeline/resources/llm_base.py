from __future__ import annotations

"""Pipeline component: llm base."""

from typing import TYPE_CHECKING

"""Public re-export of :class:`LLM`."""

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from plugins.builtin.resources.llm_base import LLM


def __getattr__(name: str):
    if name == "LLM":
        from plugins.builtin.resources.llm_base import LLM

        return LLM
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["LLM"]
