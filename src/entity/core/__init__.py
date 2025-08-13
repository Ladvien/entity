"""Entity core module - Agent and batch processing functionality."""

from .errors import (
    PipelineError,
    PluginError,
    ResourceError,
    SandboxError,
    ValidationError,
)
from .rate_limiter import (
    RateLimiter,
    create_api_rate_limiter,
    create_database_rate_limiter,
)
from .validators import (
    IdentifierValidator,
    JSONYAMLValidator,
    SQLValidator,
    TypeValidator,
)

__all__ = [
    "Agent",
    "BatchRequest",
    "BatchWorkflowExecutor",
    "PipelineError",
    "PluginError",
    "ValidationError",
    "ResourceError",
    "SandboxError",
    "RateLimiter",
    "create_api_rate_limiter",
    "create_database_rate_limiter",
    "IdentifierValidator",
    "SQLValidator",
    "JSONYAMLValidator",
    "TypeValidator",
]


def __getattr__(name: str):
    if name == "Agent":
        from .agent import Agent

        return Agent
    elif name == "BatchRequest":
        from .batch_executor import BatchRequest

        return BatchRequest
    elif name == "BatchWorkflowExecutor":
        from .batch_executor import BatchWorkflowExecutor

        return BatchWorkflowExecutor
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
