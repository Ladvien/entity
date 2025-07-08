from __future__ import annotations

"""Pipeline component: base."""

from dataclasses import dataclass


@dataclass
class RetryOptions:
    """Configuration for retrying tool executions."""

    max_retries: int = 1
    delay: float = 1.0
