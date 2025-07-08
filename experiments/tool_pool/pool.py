from __future__ import annotations

"""Experimental async pool for running tools. Not production ready."""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, List, Tuple

CallableTask = Callable[[], Awaitable[Any]]


@dataclass
class ToolPoolMetrics:
    """Simple metrics for the tool pool."""

    tasks_executed: int = 0
    total_duration: float = 0.0
    latencies: List[float] = field(default_factory=list)

    @property
    def throughput(self) -> float:
        """Average completed tasks per second."""
        if self.total_duration == 0:
            return 0.0
        return self.tasks_executed / self.total_duration

    @property
    def average_latency(self) -> float:
        if not self.latencies:
            return 0.0
        return sum(self.latencies) / len(self.latencies)


class ToolPool:
    """A minimal asynchronous execution pool for running tool callables."""

    def __init__(self, concurrency: int = 5) -> None:
        self.concurrency = concurrency
        self._queue: asyncio.Queue[Tuple[CallableTask, asyncio.Future]] = (
            asyncio.Queue()
        )
        self.metrics = ToolPoolMetrics()
        self._workers: List[asyncio.Task] = []
        self._stop = asyncio.Event()

    async def start(self) -> None:
        """Start worker tasks."""
        for _ in range(self.concurrency):
            self._workers.append(asyncio.create_task(self._worker()))

    async def stop(self) -> None:
        """Signal workers to exit and wait for them."""
        self._stop.set()
        for _ in self._workers:
            await self._queue.put(
                (lambda: asyncio.sleep(0), asyncio.get_running_loop().create_future())
            )
        await asyncio.gather(*self._workers)

    async def submit(self, task: CallableTask) -> asyncio.Future:
        """Submit a coroutine function for execution."""
        future: asyncio.Future = asyncio.get_running_loop().create_future()
        await self._queue.put((task, future))
        return future

    async def _worker(self) -> None:
        while not self._stop.is_set():
            task, future = await self._queue.get()
            if self._stop.is_set():
                if not future.done():
                    future.cancel()
                self._queue.task_done()
                continue

            start = time.perf_counter()
            try:
                result = await task()
            except Exception as exc:  # pragma: no cover - pass through
                future.set_exception(exc)
            else:
                future.set_result(result)
            duration = time.perf_counter() - start
            self.metrics.tasks_executed += 1
            self.metrics.total_duration += duration
            self.metrics.latencies.append(duration)
            self._queue.task_done()


__all__ = ["ToolPool", "ToolPoolMetrics"]
