"""Enhanced error context and debugging utilities for Entity Framework.

This module provides structured error types with rich context information,
request ID tracking, plugin stack traces, and error recovery strategies.
"""

from __future__ import annotations

import json
import traceback
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ErrorSeverity(Enum):
    """Error severity levels for classification and handling."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Categories of errors for pattern detection and recovery."""

    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RESOURCE = "resource"
    NETWORK = "network"
    TIMEOUT = "timeout"
    PLUGIN = "plugin"
    PIPELINE = "pipeline"
    SANDBOX = "sandbox"
    MEMORY = "memory"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Rich error context information for debugging."""

    request_id: str
    user_id: str
    timestamp: datetime
    stage: str
    plugin: Optional[str] = None
    plugin_stack: List[str] = field(default_factory=list)
    execution_context: Dict[str, Any] = field(default_factory=dict)
    system_state: Dict[str, Any] = field(default_factory=dict)
    recovery_attempted: bool = False
    recovery_strategies: List[str] = field(default_factory=list)


@dataclass
class PipelineError(Exception):
    """Enhanced pipeline error with rich debugging context.

    This error type provides comprehensive debugging information including
    plugin stack traces, execution context, and recovery strategies.
    """

    stage: str
    plugin: Optional[str]
    context: ErrorContext
    original_error: Exception
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    category: ErrorCategory = ErrorCategory.UNKNOWN
    recoverable: bool = True

    def __post_init__(self):
        """Initialize error message and parent exception."""
        super().__init__(str(self))

    def __str__(self) -> str:
        """Generate detailed error message with context."""
        lines = [
            f"Pipeline Error: {self.original_error.__class__.__name__}",
            f"Stage: {self.stage}",
            f"Plugin: {self.plugin or 'N/A'}",
            f"Request ID: {self.context.request_id}",
            f"User ID: {self.context.user_id}",
            f"Timestamp: {self.context.timestamp.isoformat()}",
            f"Severity: {self.severity.value}",
            f"Category: {self.category.value}",
            f"Recoverable: {self.recoverable}",
        ]

        if self.context.plugin_stack:
            lines.append(f"Plugin Stack: {' -> '.join(self.context.plugin_stack)}")

        if self.context.execution_context:
            lines.append("Execution Context:")
            lines.append(json.dumps(self.context.execution_context, indent=2))

        if self.context.recovery_attempted:
            lines.append(f"Recovery Attempted: {self.context.recovery_strategies}")

        lines.append(f"Original Error: {self.original_error}")

        # Add stack trace for debugging
        if (
            hasattr(self.original_error, "__traceback__")
            and self.original_error.__traceback__
        ):
            lines.append("Stack Trace:")
            lines.extend(traceback.format_tb(self.original_error.__traceback__))

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/serialization."""
        return {
            "error_type": "PipelineError",
            "stage": self.stage,
            "plugin": self.plugin,
            "request_id": self.context.request_id,
            "user_id": self.context.user_id,
            "timestamp": self.context.timestamp.isoformat(),
            "severity": self.severity.value,
            "category": self.category.value,
            "recoverable": self.recoverable,
            "plugin_stack": self.context.plugin_stack,
            "execution_context": self.context.execution_context,
            "system_state": self.context.system_state,
            "recovery_attempted": self.context.recovery_attempted,
            "recovery_strategies": self.context.recovery_strategies,
            "original_error": {
                "type": self.original_error.__class__.__name__,
                "message": str(self.original_error),
                "args": self.original_error.args,
            },
        }


class PluginError(PipelineError):
    """Error specific to plugin execution failures."""

    def __init__(
        self,
        plugin_name: str,
        stage: str,
        context: ErrorContext,
        original_error: Exception,
        plugin_config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            stage=stage,
            plugin=plugin_name,
            context=context,
            original_error=original_error,
            category=ErrorCategory.PLUGIN,
        )
        self.plugin_config = plugin_config or {}


class ValidationError(PipelineError):
    """Error for validation failures with detailed field information."""

    def __init__(
        self,
        field_errors: Dict[str, List[str]],
        context: ErrorContext,
        original_error: Exception,
    ):
        super().__init__(
            stage="validation",
            plugin=None,
            context=context,
            original_error=original_error,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
        )
        self.field_errors = field_errors


class ResourceError(PipelineError):
    """Error for resource-related failures (memory, database, etc)."""

    def __init__(
        self,
        resource_type: str,
        resource_id: Optional[str],
        context: ErrorContext,
        original_error: Exception,
    ):
        super().__init__(
            stage="resource",
            plugin=None,
            context=context,
            original_error=original_error,
            category=ErrorCategory.RESOURCE,
            severity=ErrorSeverity.HIGH,
        )
        self.resource_type = resource_type
        self.resource_id = resource_id


class SandboxError(PipelineError):
    """Error for sandbox execution failures."""

    def __init__(
        self,
        sandbox_type: str,
        context: ErrorContext,
        original_error: Exception,
        security_violation: bool = False,
    ):
        severity = ErrorSeverity.CRITICAL if security_violation else ErrorSeverity.HIGH
        super().__init__(
            stage="sandbox",
            plugin=None,
            context=context,
            original_error=original_error,
            category=ErrorCategory.SANDBOX,
            severity=severity,
            recoverable=not security_violation,
        )
        self.sandbox_type = sandbox_type
        self.security_violation = security_violation


class ErrorContextManager:
    """Manages error context creation and tracking throughout pipeline execution."""

    def __init__(self):
        self._active_contexts: Dict[str, ErrorContext] = {}
        self._error_patterns: Dict[str, int] = {}
        self._recovery_strategies: Dict[ErrorCategory, List[str]] = {
            ErrorCategory.VALIDATION: ["retry_with_fixed_input", "use_default_values"],
            ErrorCategory.RESOURCE: ["retry_after_delay", "use_fallback_resource"],
            ErrorCategory.NETWORK: ["retry_with_backoff", "use_cached_response"],
            ErrorCategory.TIMEOUT: ["increase_timeout", "use_async_processing"],
            ErrorCategory.PLUGIN: ["skip_plugin", "use_fallback_plugin"],
            ErrorCategory.SANDBOX: ["restart_sandbox", "use_safe_mode"],
            ErrorCategory.MEMORY: ["trigger_gc", "use_memory_efficient_mode"],
        }

    def create_context(
        self,
        user_id: str,
        stage: str,
        plugin: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> ErrorContext:
        """Create new error context for tracking."""
        if request_id is None:
            request_id = str(uuid.uuid4())

        context = ErrorContext(
            request_id=request_id,
            user_id=user_id,
            timestamp=datetime.now(),
            stage=stage,
            plugin=plugin,
        )

        self._active_contexts[request_id] = context
        return context

    def get_context(self, request_id: str) -> Optional[ErrorContext]:
        """Retrieve existing error context."""
        return self._active_contexts.get(request_id)

    def update_plugin_stack(self, request_id: str, plugin: str) -> None:
        """Add plugin to execution stack for context."""
        if context := self._active_contexts.get(request_id):
            context.plugin_stack.append(plugin)

    def add_execution_context(self, request_id: str, key: str, value: Any) -> None:
        """Add execution context information."""
        if context := self._active_contexts.get(request_id):
            context.execution_context[key] = value

    def classify_error(self, error: Exception) -> ErrorCategory:
        """Classify error into category for recovery strategy selection."""
        error_type = error.__class__.__name__.lower()
        error_message = str(error).lower()

        # Check for validation patterns first
        if (
            "validation" in error_type
            or "validation" in error_message
            or "invalid" in error_message
            or error_type in ["valueerror", "typeerror"]
        ):
            return ErrorCategory.VALIDATION
        elif "auth" in error_type or "auth" in error_message:
            if "authentication" in error_message:
                return ErrorCategory.AUTHENTICATION
            else:
                return ErrorCategory.AUTHORIZATION
        elif "resource" in error_type or "resource" in error_message:
            return ErrorCategory.RESOURCE
        elif (
            "network" in error_type
            or "connection" in error_type
            or "connection" in error_message
            or error_type == "connectionerror"
        ):
            return ErrorCategory.NETWORK
        elif "timeout" in error_type or "timeout" in error_message:
            return ErrorCategory.TIMEOUT
        elif "sandbox" in error_type or "sandbox" in error_message:
            return ErrorCategory.SANDBOX
        elif "memory" in error_type or "memory" in error_message:
            return ErrorCategory.MEMORY
        else:
            return ErrorCategory.UNKNOWN

    def get_recovery_strategies(self, category: ErrorCategory) -> List[str]:
        """Get available recovery strategies for error category."""
        return self._recovery_strategies.get(category, [])

    def record_error_pattern(self, error_signature: str) -> None:
        """Record error pattern for trend analysis."""
        self._error_patterns[error_signature] = (
            self._error_patterns.get(error_signature, 0) + 1
        )

    def get_error_patterns(self) -> Dict[str, int]:
        """Get error pattern statistics."""
        return self._error_patterns.copy()

    def create_pipeline_error(
        self,
        stage: str,
        plugin: Optional[str],
        original_error: Exception,
        context: ErrorContext,
        severity: Optional[ErrorSeverity] = None,
    ) -> PipelineError:
        """Create appropriate pipeline error with classification."""
        category = self.classify_error(original_error)

        if severity is None:
            severity = self._determine_severity(category, original_error)

        # Record error pattern
        error_signature = f"{category.value}:{original_error.__class__.__name__}"
        self.record_error_pattern(error_signature)

        return PipelineError(
            stage=stage,
            plugin=plugin,
            context=context,
            original_error=original_error,
            severity=severity,
            category=category,
            recoverable=self._is_recoverable(category),
        )

    def _determine_severity(
        self, category: ErrorCategory, error: Exception
    ) -> ErrorSeverity:
        """Determine error severity based on category and error type."""
        if category in [ErrorCategory.SANDBOX]:
            return ErrorSeverity.CRITICAL
        elif category in [ErrorCategory.RESOURCE, ErrorCategory.MEMORY]:
            return ErrorSeverity.HIGH
        elif category in [
            ErrorCategory.PLUGIN,
            ErrorCategory.NETWORK,
            ErrorCategory.TIMEOUT,
        ]:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW

    def _is_recoverable(self, category: ErrorCategory) -> bool:
        """Determine if error category is generally recoverable."""
        non_recoverable = {ErrorCategory.AUTHENTICATION, ErrorCategory.AUTHORIZATION}
        return category not in non_recoverable

    def cleanup_context(self, request_id: str) -> None:
        """Clean up completed error context."""
        self._active_contexts.pop(request_id, None)


# Global error context manager instance
error_context_manager = ErrorContextManager()
