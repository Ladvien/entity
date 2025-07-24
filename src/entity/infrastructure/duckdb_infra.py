from __future__ import annotations

from contextlib import contextmanager
from queue import Empty, Full, Queue
from typing import Generator


class DuckDBInfrastructure:
    """Layer 1 infrastructure for managing a DuckDB database file."""

    def __init__(self, file_path: str, pool_size: int = 5) -> None:
        """Create the infrastructure with a simple connection pool."""

        self.file_path = file_path
        self._pool: Queue = Queue(maxsize=pool_size)

    def _acquire(self):
        import duckdb

        try:
            return self._pool.get_nowait()
        except Empty:  # No available connection
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

    def health_check(self) -> bool:
        """Return ``True`` if the database can be opened."""
        try:
            with self.connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception:
            return False
