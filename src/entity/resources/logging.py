from __future__ import annotations

from typing import Any, Dict, List


class LoggingResource:
    """Collect log entries for later inspection."""

    def __init__(self) -> None:
        """Initialize an empty list of log records."""

        self.records: List[Dict[str, Any]] = []

    async def log(self, level: str, message: str, **fields: Any) -> None:
        """Store a log entry with arbitrary metadata."""
        entry = {"level": level, "message": message, **fields}
        self.records.append(entry)
