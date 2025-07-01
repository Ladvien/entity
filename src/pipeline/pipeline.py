"""Compatibility wrappers for pipeline execution."""

from __future__ import annotations

from .execution import (
    create_default_response,
    execute_pipeline,
    execute_stage,
    generate_pipeline_id,
)
from .tools.execution import execute_pending_tools

__all__ = [
    "generate_pipeline_id",
    "create_default_response",
    "execute_stage",
    "execute_pipeline",
    "execute_pending_tools",
]
