from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ToolInfo:
    """Metadata about a registered tool."""

    name: str
    func: Callable[..., Any]
    category: Optional[str] = None
    description: Optional[str] = None


_REGISTRY: Dict[str, ToolInfo] = {}


def register_tool(
    func: Callable[..., Any],
    name: Optional[str] = None,
    *,
    category: Optional[str] = None,
    description: Optional[str] = None,
) -> None:
    """Register ``func`` under ``name`` with optional metadata."""
    tool_name = name or func.__name__
    _REGISTRY[tool_name] = ToolInfo(tool_name, func, category, description)


def discover_tools(category: Optional[str] = None) -> List[ToolInfo]:
    """Return tools filtered by ``category`` if provided."""
    if category is None:
        return list(_REGISTRY.values())
    return [tool for tool in _REGISTRY.values() if tool.category == category]


def clear_registry() -> None:
    """Remove all registered tools (mainly for tests)."""
    _REGISTRY.clear()


__all__ = ["register_tool", "discover_tools", "ToolInfo", "clear_registry"]
