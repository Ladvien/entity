"""GPT-OSS specific plugins for Entity Framework."""

from .reasoning_trace import ReasoningTracePlugin
from .structured_output import StructuredOutputPlugin

__all__ = ["ReasoningTracePlugin", "StructuredOutputPlugin"]
