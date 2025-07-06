"""Simplified plugin examples using composition."""

from .prompt import ComposedPrompt
from .resource import ComposedResource
from .tool import ComposedTool

__all__ = ["ComposedPrompt", "ComposedResource", "ComposedTool"]
