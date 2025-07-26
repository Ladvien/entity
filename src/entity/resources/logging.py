from __future__ import annotations

import asyncio
import json
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


@dataclass
class LogRecord:
    level: str
    message: str
    timestamp: str
    fields: Dict[str, Any]


class LoggingResource:
    """Collect structured log entries with level filtering."""

    LEVELS = {"debug": 10, "info": 20, "warning": 30, "error": 40}

    def __init__(self, level: str = "info") -> None:
        self.level = level
        self.records: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()

    def health_check(self) -> bool:
        """Always returns ``True`` as logging has no external deps."""

        return True

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
            message=message,
            timestamp=datetime.utcnow().isoformat(),
            fields=fields,
        )
        async with self._lock:
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
