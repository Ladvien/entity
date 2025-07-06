from __future__ import annotations

"""Public re-export of :class:`LLMResource`."""


def __getattr__(name: str):
    if name == "LLMResource":
        from plugins.builtin.resources.llm_resource import LLMResource

        return LLMResource
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["LLMResource"]
