import asyncio
import json
import os
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

from rich.console import Console


class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class LogCategory(Enum):
    PLUGIN_LIFECYCLE = "plugin_lifecycle"
    USER_ACTION = "user_action"
    RESOURCE_ACCESS = "resource_access"
    TOOL_USAGE = "tool_usage"
    MEMORY_OPERATION = "memory_operation"
    WORKFLOW_EXECUTION = "workflow_execution"
    PERFORMANCE = "performance"
    ERROR = "error"


@dataclass
class LogContext:
    """Contextual fields automatically injected into each log entry."""

    user_id: str
    workflow_id: str | None = None
    stage: str | None = None
    plugin_name: str | None = None
    execution_id: str | None = None


@dataclass
class LogRecord:
    level: str
    message: str
    timestamp: str
    fields: Dict[str, Any]


class EnhancedLoggingResource(ABC):
    """Enhanced logging with automatic context and structured output."""

    LEVELS = {
        LogLevel.DEBUG: 10,
        LogLevel.INFO: 20,
        LogLevel.WARNING: 30,
        LogLevel.ERROR: 40,
    }

    def __init__(self, level: LogLevel = LogLevel.INFO) -> None:
        self.level = level
        self.records: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()

    def health_check(self) -> bool:
        return True

    def _should_log(self, level: LogLevel) -> bool:
        return self.LEVELS[level] >= self.LEVELS[self.level]

    @abstractmethod
    async def log(
        self,
        level: LogLevel,
        category: LogCategory,
        message: str,
        context: LogContext | None = None,
        **extra_fields: Any,
    ) -> None:
        """Log structured entry with automatic context injection."""


class RichConsoleLoggingResource(EnhancedLoggingResource):
    """Colored, formatted console logging using Rich."""

    _styles = {
        LogLevel.DEBUG: "cyan",
        LogLevel.INFO: "green",
        LogLevel.WARNING: "yellow",
        LogLevel.ERROR: "red",
    }

    def __init__(
        self, level: LogLevel = LogLevel.INFO, show_context: bool = True
    ) -> None:
        super().__init__(level)
        self.show_context = show_context
        self.console = Console()

    def _format_console_entry(
        self,
        level: LogLevel,
        category: LogCategory,
        message: str,
        context: LogContext | None,
        extra_fields: Dict[str, Any],
    ) -> str:
        style = self._styles[level]
        parts = [f"[{style}][{level.value}] {message}[/]"]
        parts.append(f"({category.value})")
        if self.show_context and context is not None:
            ctx = {k: v for k, v in asdict(context).items() if v is not None}
            if ctx:
                parts.append(" " + ", ".join(f"{k}={v}" for k, v in ctx.items()))
        if extra_fields:
            parts.append(" " + ", ".join(f"{k}={v}" for k, v in extra_fields.items()))
        return "".join(parts)

    async def log(
        self,
        level: LogLevel,
        category: LogCategory,
        message: str,
        context: LogContext | None = None,
        **extra_fields: Any,
    ) -> None:
        if not self._should_log(level):
            return
        entry = {
            "level": level.value,
            "category": category.value,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "fields": extra_fields,
        }
        if context is not None:
            entry["context"] = {
                k: v for k, v in asdict(context).items() if v is not None
            }
        formatted = self._format_console_entry(
            level, category, message, context, extra_fields
        )
        self.console.print(formatted)
        async with self._lock:
            self.records.append(entry)


class RichJSONLoggingResource(EnhancedLoggingResource):
    """Structured JSON logging with optional Rich console output."""

    def __init__(
        self,
        level: LogLevel = LogLevel.INFO,
        output_file: str | None = None,
        max_bytes: int = 0,
        backup_count: int = 0,
    ) -> None:
        super().__init__(level)
        self.output_file = output_file
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.console = Console()

    async def _rotate_if_needed(self) -> None:
        if not self.output_file or self.max_bytes <= 0:
            return
        if not os.path.exists(self.output_file):
            return
        if os.path.getsize(self.output_file) < self.max_bytes:
            return
        timestamp = int(time.time())
        rotated = f"{self.output_file}.{timestamp}"
        os.rename(self.output_file, rotated)
        if self.backup_count > 0:
            backups = sorted(
                [
                    f
                    for f in os.listdir(os.path.dirname(self.output_file))
                    if f.startswith(os.path.basename(self.output_file) + ".")
                ]
            )
            while len(backups) > self.backup_count:
                os.remove(
                    os.path.join(os.path.dirname(self.output_file), backups.pop(0))
                )

    async def _write_entry(self, entry: Dict[str, Any]) -> None:
        data = json.dumps(entry, ensure_ascii=False)
        if self.output_file:
            await self._rotate_if_needed()
            async with self._lock:
                with open(self.output_file, "a", encoding="utf-8") as fh:
                    fh.write(data + "\n")
        else:
            self.console.print_json(data)
        async with self._lock:
            self.records.append(entry)

    async def log(
        self,
        level: LogLevel,
        category: LogCategory,
        message: str,
        context: LogContext | None = None,
        **extra_fields: Any,
    ) -> None:
        if not self._should_log(level):
            return
        entry = {
            "level": level.value,
            "category": category.value,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "fields": extra_fields,
        }
        if context is not None:
            entry["context"] = {
                k: v for k, v in asdict(context).items() if v is not None
            }
        await self._write_entry(entry)
