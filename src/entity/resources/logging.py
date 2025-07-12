from __future__ import annotations

"""Unified logging resource with multiple outputs."""

import asyncio
import json
import logging
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
    """Append structured logs to a JSON Lines file."""

    def __init__(self, path: str, level: int) -> None:
        super().__init__(level)
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.path.open("a", encoding="utf-8")
        self._lock = asyncio.Lock()

    async def write(self, entry: Dict[str, Any]) -> None:
        async with self._lock:
            self._handle.write(json.dumps(entry) + "\n")
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
        import websockets

        self.server = await websockets.serve(self._handler, self.host, self.port)
        # Capture actual port when 0 was provided
        self.port = self.server.sockets[0].getsockname()[1]

    async def stop(self) -> None:
        if self.server is None:
            return
        self.server.close()
        await self.server.wait_closed()

    async def _handler(self, websocket: Any, _path: str) -> None:
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

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        super().__init__(config or {})
        self._outputs: List[LogOutput] = []
        self._stream_outputs: List[StreamLogOutput] = []

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
                self._outputs.append(StructuredFileOutput(path, level))
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
        }
        if extra:
            entry.update(extra)

        level_no = _level(level)
        for output in self._outputs:
            if level_no >= output.level:
                await output.write(entry)


__all__ = ["LoggingResource"]
