"""GPT-OSS specific plugins for Entity Framework."""

from .native_tools import GPTOSSToolOrchestrator
from .reasoning_trace import ReasoningTracePlugin

__all__ = ["ReasoningTracePlugin", "GPTOSSToolOrchestrator"]
