from __future__ import annotations

from contextlib import contextmanager
from queue import Empty, Full, Queue
from typing import Generator

from .base import BaseInfrastructure


class DuckDBInfrastructure(BaseInfrastructure):
    """Layer 1 infrastructure for managing a DuckDB database file."""

    def __init__(
        self, file_path: str, pool_size: int = 5, version: str | None = None
    ) -> None:
        """Create the infrastructure with a simple connection pool."""

        super().__init__(version)
        self.file_path = file_path
        if file_path == ":memory:":
            self._pool = Queue(maxsize=1)
            import duckdb

            self._pool.put_nowait(duckdb.connect(file_path))
        else:
            self._pool = Queue(maxsize=pool_size)

    def _acquire(self):
        import duckdb

        try:
            return self._pool.get_nowait()
        except Empty:  # No available connection
            if self.file_path == ":memory:":
                return self._pool.get()
            return duckdb.connect(self.file_path)

    def _release(self, conn) -> None:
        try:
            self._pool.put_nowait(conn)
        except Full:
            conn.close()

    @contextmanager
    def connect(self) -> Generator:  # pragma: no cover - thin wrapper
        """Yield a database connection from the pool."""

        conn = self._acquire()
        try:
            yield conn
        finally:
            self._release(conn)

    async def startup(self) -> None:  # pragma: no cover - thin wrapper
        await super().startup()
        self.logger.info("DuckDB file %s ready", self.file_path)

    async def shutdown(self) -> None:  # pragma: no cover - thin wrapper
        await super().shutdown()
        while not self._pool.empty():
            self._pool.get_nowait().close()

    def health_check(self) -> bool:
        """Return ``True`` if the database can be opened."""
        try:
            with self.connect() as conn:
                conn.execute("SELECT 1")
            self.logger.debug("Health check succeeded for %s", self.file_path)
            return True
        except Exception as exc:
            self.logger.warning("Health check failed for %s: %s", self.file_path, exc)
            return False
