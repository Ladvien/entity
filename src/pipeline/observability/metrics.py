from __future__ import annotations

"""Stubbed metrics integration for the Entity pipeline."""

from entity.core.state import MetricsCollector

__all__ = ["MetricsServer", "MetricsServerManager"]


class MetricsServer:
    """Placeholder metrics server."""

    def __init__(self, port: int = 9001) -> None:  # pragma: no cover - simple init
        self.port = port

    def update(self, metrics: MetricsCollector) -> None:  # pragma: no cover - noop
        pass

    def render(self) -> bytes:  # pragma: no cover - noop
        return b""


class MetricsServerManager:
    """Manage a single :class:`MetricsServer` instance."""

    _server: MetricsServer | None = None

    @classmethod
    def start(cls, port: int = 9001) -> MetricsServer:
        """Create the metrics server if not already running."""

        if cls._server is None:
            cls._server = MetricsServer(port)
        return cls._server

    @classmethod
    def get(cls) -> MetricsServer | None:
        """Return the active :class:`MetricsServer` instance if running."""

        return cls._server
