from __future__ import annotations

import asyncio
import json
<<<<<<< HEAD
<<<<<<< HEAD
=======
import sys
>>>>>>> pr-1950
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


@dataclass
class LogLevel(Enum):
    """Supported log levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class LogCategory(Enum):
    """High level categories for structured log events."""

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
    workflow_id: Optional[str] = None
    stage: Optional[str] = None
    plugin_name: Optional[str] = None
    execution_id: Optional[str] = None
=======
import os
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List
>>>>>>> pr-1948


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
    """Automatic context injected into every log entry."""

    user_id: str
    workflow_id: str | None = None
    stage: str | None = None
    plugin_name: str | None = None
    execution_id: str | None = None


@dataclass
class LogRecord:
    level: LogLevel
    category: LogCategory
    message: str
    timestamp: str
    context: LogContext | None
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

<<<<<<< HEAD
    async def log(
        self,
        level: LogLevel,
        category: LogCategory,
        message: str,
        context: LogContext | None = None,
        **extra_fields: Any,
    ) -> None:
        """Store a log entry if ``level`` is above the configured threshold."""

        level_str = level.value
        if self.LEVELS.get(level_str, 0) < self.LEVELS.get(self.level, 0):
            return

        fields: Dict[str, Any] = {"category": category.value}
        if context is not None:
            fields.update({k: v for k, v in asdict(context).items() if v is not None})
        fields.update(extra_fields)

        record = LogRecord(
            level=level_str,
=======
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


class ConsoleLoggingResource(EnhancedLoggingResource):
    """Colored, formatted console logging for development."""

    _colors = {
        LogLevel.DEBUG: "\033[36m",
        LogLevel.INFO: "\033[32m",
        LogLevel.WARNING: "\033[33m",
        LogLevel.ERROR: "\033[31m",
    }
    _reset = "\033[0m"

    def __init__(
        self, level: LogLevel = LogLevel.INFO, show_context: bool = True
    ) -> None:
        super().__init__(level)
        self.show_context = show_context

    def _format_console_entry(
        self,
        level: LogLevel,
        category: LogCategory,
        message: str,
        context: LogContext | None,
        extra_fields: Dict[str, Any],
    ) -> str:
        color = self._colors[level]
        parts = [f"{color}[{level.value}] {message}{self._reset}"]
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
        entry = LogRecord(
            level=level,
            category=category,
>>>>>>> pr-1948
            message=message,
            timestamp=datetime.utcnow().isoformat(),
            context=context,
            fields=extra_fields,
        )
        formatted = self._format_console_entry(
            level, category, message, context, extra_fields
        )
        print(formatted)
        async with self._lock:
<<<<<<< HEAD
            self.records.append(asdict(record))


class ConsoleLoggingResource(LoggingResource):
<<<<<<< HEAD
    """Store logs in memory like ``LoggingResource``."""

    async def log(self, level: str, message: str, **fields: Any) -> None:
        await super().log(level, message, **fields)


class JSONLoggingResource(LoggingResource):
    """Append log entries to ``path`` in JSON lines format."""

    def __init__(self, path: str, level: str = "info") -> None:
        super().__init__(level)
        self.path = path

    async def log(self, level: str, message: str, **fields: Any) -> None:
        await super().log(level, message, **fields)
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(self.records[-1]) + "\n")
=======
    """Logging resource that echoes entries to ``stream`` in human format."""

    def __init__(self, level: str = "info", stream: Any | None = None) -> None:
        super().__init__(level)
        self.stream = stream or sys.stdout

    async def log(self, level: str, message: str, **fields: Any) -> None:
        await super().log(level, message, **fields)
        if self.LEVELS.get(level, 0) >= self.LEVELS.get(self.level, 0):
            text = f"{level.upper()}: {message} {fields}\n"
            self.stream.write(text)
            self.stream.flush()


class JSONLoggingResource(LoggingResource):
    """Logging resource that emits JSON log lines to ``stream``."""

    def __init__(self, level: str = "info", stream: Any | None = None) -> None:
        super().__init__(level)
        self.stream = stream or sys.stdout

    async def log(self, level: str, message: str, **fields: Any) -> None:
        await super().log(level, message, **fields)
        if self.LEVELS.get(level, 0) >= self.LEVELS.get(self.level, 0):
            record = {
                "level": level,
                "message": message,
                "fields": fields,
            }
            self.stream.write(json.dumps(record) + "\n")
            self.stream.flush()
>>>>>>> pr-1950
=======
            self.records.append(asdict(entry))


class JSONLoggingResource(EnhancedLoggingResource):
    """Structured JSON logging for production environments."""

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
            print(data)
        async with self._lock:
            self.records.append(entry)

    def _build_json_entry(
        self,
        level: LogLevel,
        category: LogCategory,
        message: str,
        context: LogContext | None,
        extra_fields: Dict[str, Any],
    ) -> Dict[str, Any]:
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
        return entry

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
        entry = self._build_json_entry(level, category, message, context, extra_fields)
        await self._write_entry(entry)
>>>>>>> pr-1948
