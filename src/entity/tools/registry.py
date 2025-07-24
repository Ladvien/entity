from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Type

from pydantic import BaseModel


@dataclass
class ToolInfo:
    """Metadata about a registered tool."""

    name: str
    func: Callable[..., Any]
    category: Optional[str] = None
    description: Optional[str] = None
    input_model: Type[BaseModel] | None = None
    output_model: Type[BaseModel] | None = None


_REGISTRY: Dict[str, ToolInfo] = {}


def register_tool(
    func: Callable[..., Any],
    name: Optional[str] = None,
    *,
    category: Optional[str] = None,
    description: Optional[str] = None,
    input_model: Type[BaseModel] | None = None,
    output_model: Type[BaseModel] | None = None,
) -> None:
    """Register ``func`` under ``name`` with optional metadata."""
    tool_name = name or func.__name__
    _REGISTRY[tool_name] = ToolInfo(
        tool_name,
        func,
        category,
        description,
        input_model,
        output_model,
    )


def discover_tools(category: Optional[str] = None) -> List[ToolInfo]:
    """Return tools filtered by ``category`` if provided."""
    if category is None:
        return list(_REGISTRY.values())
    return [tool for tool in _REGISTRY.values() if tool.category == category]


def clear_registry() -> None:
    """Remove all registered tools (mainly for tests)."""
    _REGISTRY.clear()


def generate_docs() -> str:
    """Return Markdown table documenting all registered tools."""
    headers = "| Name | Description | Category |\n|------|-------------|----------|"
    lines = [headers]
    for info in discover_tools():
        desc = info.description or ""
        cat = info.category or ""
        lines.append(f"| {info.name} | {desc} | {cat} |")
    return "\n".join(lines)


__all__ = [
    "register_tool",
    "discover_tools",
    "ToolInfo",
    "clear_registry",
    "generate_docs",
]
