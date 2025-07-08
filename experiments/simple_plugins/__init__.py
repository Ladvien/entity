"""Simplified plugin examples using composition. Not for production."""

from .prompt import ComposedPrompt
from .resource import ComposedResource
from .tool import ComposedTool

__all__ = ["ComposedPrompt", "ComposedResource", "ComposedTool"]
