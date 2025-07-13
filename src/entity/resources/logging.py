from __future__ import annotations

"""Unified logging resource with multiple outputs."""

import asyncio
import json
import logging
import os
import socket
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import AgentResource
from entity.config.models import LoggingConfig
from pydantic import ValidationError
from entity.core.plugins import ValidationResult


def _level(name: str) -> int:
    """Return numeric logging level for ``name``."""
    return logging._nameToLevel.get(name.upper(), logging.INFO)


def _parse_size(value: str | int | None) -> int | None:
    """Return bytes from ``value`` supporting ``KB``, ``MB``, ``GB`` suffixes."""
    if value is None:
        return None
    if isinstance(value, int):
        return value
    multipliers = {"kb": 1024, "mb": 1024**2, "gb": 1024**3}
    value = value.strip().lower()
    for suffix, mult in multipliers.items():
        if value.endswith(suffix):
            return int(float(value[:-2]) * mult)
    return int(value)


@dataclass
class LogEntry:
    timestamp: str
    level: str
    message: str
    component: str
    user_id: Optional[str]
    pipeline_id: Optional[str]
    stage: Optional[str]
    plugin_name: Optional[str]
    resource_name: Optional[str]
    extra: Dict[str, Any]


class LogOutput:
    """Base class for log outputs."""

    def __init__(self, level: int) -> None:
        self.level = level

    async def write(
        self, entry: Dict[str, Any]
    ) -> None:  # pragma: no cover - interface
        raise NotImplementedError


class ConsoleLogOutput(LogOutput):
    """Write logs to standard output."""

    async def write(self, entry: Dict[str, Any]) -> None:
        msg = (
            f"[{entry['timestamp']}] {entry['level'].upper()} "
            f"{entry['component']}: {entry['message']}"
        )
        print(msg)


class StructuredFileOutput(LogOutput):
    """Append structured logs to a JSON Lines file with optional rotation."""

    def __init__(
        self, path: str, level: int, max_bytes: int = 0, backup_count: int = 0
    ) -> None:
        super().__init__(level)
        self.path = Path(path)
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.path.open("a", encoding="utf-8")
        self._lock = asyncio.Lock()

    def _should_rotate(self, additional_bytes: int = 0) -> bool:
        """Return True if writing ``additional_bytes`` would exceed ``max_bytes``."""
        if self.max_bytes <= 0:
            return False
        self._handle.flush()
        return (self.path.stat().st_size + additional_bytes) >= self.max_bytes

    def _rotate(self) -> None:
        self._handle.close()
        if self.backup_count > 0:
            for i in range(self.backup_count - 1, 0, -1):
                src = self.path.with_name(f"{self.path.name}.{i}")
                dst = self.path.with_name(f"{self.path.name}.{i + 1}")
                if src.exists():
                    src.rename(dst)
            rotate_target = self.path.with_name(f"{self.path.name}.1")
            if self.path.exists():
                self.path.rename(rotate_target)
        else:
            if self.path.exists():
                self.path.unlink()
        self._handle = self.path.open("a", encoding="utf-8")

    async def write(self, entry: Dict[str, Any]) -> None:
        async with self._lock:
            data = json.dumps(entry) + "\n"
            if self._should_rotate(len(data.encode("utf-8"))):
                self._rotate()
            self._handle.write(data)
            self._handle.flush()

    def close(self) -> None:
        self._handle.close()


class StreamLogOutput(LogOutput):
    """Broadcast log entries over a WebSocket."""

    def __init__(self, host: str, port: int, level: int) -> None:
        super().__init__(level)
        self.host = host
        self.port = port
        self.server: Any | None = None
        self.clients: set[Any] = set()

    async def start(self) -> None:
        if self.server is not None:
            return
        import websockets

        self.server = await websockets.serve(self._handler, self.host, self.port)
        # Capture actual port when 0 was provided
        self.port = self.server.sockets[0].getsockname()[1]

    async def stop(self) -> None:
        if self.server is None:
            return
        self.server.close()
        await self.server.wait_closed()

    async def _handler(self, websocket: Any, *_path: Any) -> None:
        self.clients.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            self.clients.discard(websocket)

    async def write(self, entry: Dict[str, Any]) -> None:
        if self.server is None:
            return
        message = json.dumps(entry)
        for ws in list(self.clients):
            try:
                await ws.send(message)
            except Exception:  # pragma: no cover - best effort
                self.clients.discard(ws)


class LoggingResource(AgentResource):
    """Canonical logging resource with async ``log`` API."""

    name = "logging"
    dependencies: List[str] = []
    infrastructure_dependencies: List[str] = []
    resource_category = "filesystem"

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        super().__init__(config or {})
        self._outputs: List[LogOutput] = []
        self._stream_outputs: List[StreamLogOutput] = []
        self.host_name = self.config.get("host_name", socket.gethostname())
        self.process_id = self.config.get("process_id", os.getpid())

    @classmethod
    async def validate_config(cls, config: Dict[str, Any]) -> ValidationResult:
        try:
            LoggingConfig.parse_obj(config)
        except ValidationError as exc:
            return ValidationResult.error_result(str(exc))
        return ValidationResult.success_result()

    async def initialize(self) -> None:
        outputs_cfg = self.config.get("outputs", [{"type": "console"}])
        for out in outputs_cfg:
            otype = out.get("type", "console")
            level = _level(out.get("level", "INFO"))
            if otype == "console":
                self._outputs.append(ConsoleLogOutput(level))
            elif otype in {"structured_file", "file"}:
                path = out.get("path", "agent.log")
                size = _parse_size(out.get("max_bytes", out.get("max_size", 0)))
                max_bytes = 0 if size is None else size
                backup_count = int(out.get("backup_count", 0))
                self._outputs.append(
                    StructuredFileOutput(path, level, max_bytes, backup_count)
                )
            elif otype in {"real_time_stream", "stream"}:
                host = out.get("host", "127.0.0.1")
                port = int(out.get("port", 0))
                stream = StreamLogOutput(host, port, level)
                await stream.start()
                self._outputs.append(stream)
                self._stream_outputs.append(stream)

    async def shutdown(self) -> None:
        for out in self._outputs:
            close = getattr(out, "close", None)
            if callable(close):
                close()
        for stream in self._stream_outputs:
            await stream.stop()

    async def log(
        self,
        level: str,
        message: str,
        *,
        component: str,
        user_id: str | None = None,
        pipeline_id: str | None = None,
        stage: Any | None = None,
        plugin_name: str | None = None,
        resource_name: str | None = None,
        correlation_headers: Dict[str, Any] | None = None,
        **extra: Any,
    ) -> None:
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level.lower(),
            "message": message,
            "component": component,
            "user_id": user_id,
            "pipeline_id": pipeline_id,
            "stage": str(stage) if stage is not None else None,
            "plugin_name": plugin_name,
            "resource_name": resource_name,
            "host": self.host_name,
            "pid": self.process_id,
        }
        if extra:
            entry.update(extra)

        level_no = _level(level)
        for output in self._outputs:
            if level_no >= output.level:
                await output.write(entry)


__all__ = ["LoggingResource"]
