from __future__ import annotations

"""Pipeline component: llm resource."""

from typing import TYPE_CHECKING

"""Public re-export of :class:`LLMResource`."""

# Load the real LLM resource only when requested.

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from plugins.builtin.resources.llm_resource import LLMResource


def __getattr__(name: str):
    if name == "LLMResource":
        from plugins.builtin.resources.llm_resource import LLMResource

        return LLMResource
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["LLMResource"]
