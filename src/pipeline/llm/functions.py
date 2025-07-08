from __future__ import annotations

"""Pipeline component: functions."""

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class FunctionCall:
    """Model-invoked function call description."""

    name: str
    arguments: Dict[str, Any] = field(default_factory=dict)
