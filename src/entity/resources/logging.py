from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List


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

    async def log(self, level: str, message: str, **fields: Any) -> None:
        """Store a log entry if ``level`` is above the configured threshold."""

        if self.LEVELS.get(level, 0) < self.LEVELS.get(self.level, 0):
            return
        record = LogRecord(
            level=level,
            message=message,
            timestamp=datetime.utcnow().isoformat(),
            fields=fields,
        )
        async with self._lock:
            self.records.append(asdict(record))


class ConsoleLoggingResource(LoggingResource):
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
