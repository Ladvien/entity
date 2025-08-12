"""Request batching system for efficient pipeline processing."""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from entity.resources.logging import LogCategory, LogLevel
from entity.workflow.executor import WorkflowExecutor


class Priority(Enum):
    """Request priority levels for queuing."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class BatchRequest:
    """Represents a single request in the batch queue."""

    message: str
    user_id: str
    priority: Priority = Priority.NORMAL
    timestamp: float = field(default_factory=time.time)
    future: asyncio.Future[str] = field(default_factory=asyncio.Future)
    context_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BatchMetrics:
    """Metrics for batch processing efficiency."""

    total_batches_processed: int = 0
    total_requests_processed: int = 0
    avg_batch_size: float = 0.0
    avg_batch_processing_time: float = 0.0
    avg_request_wait_time: float = 0.0
    timeouts: int = 0
    priority_distribution: Dict[Priority, int] = field(
        default_factory=lambda: defaultdict(int)
    )

    def update_batch_metrics(
        self, batch_size: int, processing_time: float, wait_times: List[float]
    ) -> None:
        """Update metrics after processing a batch."""
        self.total_batches_processed += 1
        self.total_requests_processed += batch_size

        total_batches = self.total_batches_processed
        self.avg_batch_size = (
            (self.avg_batch_size * (total_batches - 1)) + batch_size
        ) / total_batches
        self.avg_batch_processing_time = (
            (self.avg_batch_processing_time * (total_batches - 1)) + processing_time
        ) / total_batches

        if wait_times:
            avg_wait = sum(wait_times) / len(wait_times)
            total_requests = self.total_requests_processed
            self.avg_request_wait_time = (
                (self.avg_request_wait_time * (total_requests - batch_size))
                + (avg_wait * batch_size)
            ) / total_requests


class BatchWorkflowExecutor(WorkflowExecutor):
    """Extended workflow executor with request batching capabilities.

    This executor maintains a queue of incoming requests and processes them in batches
    to improve throughput in high-concurrency scenarios. It supports adaptive batching,
    priority queuing, and comprehensive metrics collection.

    Key Features:
    - Configurable batch size and timeout
    - Priority-based request queuing
    - Adaptive batching based on load
    - Request isolation within batches
    - Comprehensive metrics collection
    - Graceful degradation under low load
    """

    def __init__(
        self,
        resources: Dict[str, Any],
        workflow: Optional["Workflow"] = None,
        batch_size: int = 10,
        batch_timeout: float = 0.1,
        max_queue_size: int = 1000,
        adaptive_batching: bool = True,
        priority_enabled: bool = True,
    ) -> None:
        """Initialize the batch workflow executor.

        Args:
            resources: Dictionary of available resources
            workflow: Workflow configuration
            batch_size: Maximum number of requests to process in a single batch
            batch_timeout: Maximum time to wait for a batch to fill (seconds)
            max_queue_size: Maximum number of queued requests
            adaptive_batching: Enable adaptive batch sizing based on load
            priority_enabled: Enable priority-based queuing
        """
        super().__init__(resources, workflow)

        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.max_queue_size = max_queue_size
        self.adaptive_batching = adaptive_batching
        self.priority_enabled = priority_enabled

        self._request_queue: asyncio.Queue[BatchRequest] = asyncio.Queue(
            maxsize=max_queue_size
        )
        self._priority_queues: Dict[Priority, List[BatchRequest]] = {
            priority: [] for priority in Priority
        }
        self._processing_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()

        self._metrics = BatchMetrics()
        self._load_history: List[float] = []
        self._last_batch_time = time.time()

        self._min_batch_size = max(1, batch_size // 4)
        self._max_batch_size = batch_size * 2
        self._load_window_size = 10

    async def start_batch_processing(self) -> None:
        """Start the background batch processing task."""
        if self._processing_task is None or self._processing_task.done():
            self._processing_task = asyncio.create_task(self._batch_processor())

            if "logging" in self.resources:
                await self.resources["logging"].log(
                    LogLevel.INFO,
                    LogCategory.SYSTEM,
                    "Batch processing started",
                    batch_size=self.batch_size,
                    batch_timeout=self.batch_timeout,
                    adaptive_batching=self.adaptive_batching,
                )

    async def stop_batch_processing(self) -> None:
        """Stop the background batch processing task gracefully."""
        self._shutdown_event.set()

        if self._processing_task and not self._processing_task.done():
            try:
                await asyncio.wait_for(self._processing_task, timeout=5.0)
            except asyncio.TimeoutError:
                self._processing_task.cancel()
                try:
                    await self._processing_task
                except asyncio.CancelledError:
                    pass

        await self._flush_remaining_requests()

        if "logging" in self.resources:
            await self.resources["logging"].log(
                LogLevel.INFO,
                LogCategory.SYSTEM,
                "Batch processing stopped",
                final_metrics=self.get_batch_metrics(),
            )

    async def execute_batch(
        self,
        message: str,
        user_id: str = "default",
        priority: Priority = Priority.NORMAL,
        timeout: Optional[float] = None,
    ) -> str:
        """Execute a request through the batch processing system.

        Args:
            message: Input message to process
            user_id: User identifier for the request
            priority: Priority level for request queuing
            timeout: Maximum time to wait for processing

        Returns:
            Processed response string

        Raises:
            asyncio.TimeoutError: If request times out
            asyncio.QueueFull: If the request queue is full
        """
        await self.start_batch_processing()

        request = BatchRequest(
            message=message,
            user_id=user_id,
            priority=priority,
        )

        self._metrics.priority_distribution[priority] += 1

        try:
            if self.priority_enabled:
                await self._enqueue_priority_request(request)
            else:
                await self._request_queue.put(request)

            if timeout:
                return await asyncio.wait_for(request.future, timeout=timeout)
            else:
                return await request.future

        except asyncio.TimeoutError:
            self._metrics.timeouts += 1
            if not request.future.done():
                request.future.cancel()
            raise

    async def _enqueue_priority_request(self, request: BatchRequest) -> None:
        """Add request to priority queue and signal batch processor."""
        self._priority_queues[request.priority].append(request)

        try:
            self._request_queue.put_nowait(request)
        except asyncio.QueueFull:
            self._priority_queues[request.priority].remove(request)
            raise

    async def _batch_processor(self) -> None:
        """Main batch processing loop."""
        while not self._shutdown_event.is_set():
            try:
                batch = await self._collect_batch()

                if batch:
                    await self._process_batch(batch)

                    if self.adaptive_batching:
                        current_load = len(batch) / self.batch_size
                        self._update_load_history(current_load)

            except asyncio.CancelledError:
                break
            except Exception as exc:
                if "logging" in self.resources:
                    await self.resources["logging"].log(
                        LogLevel.ERROR,
                        LogCategory.SYSTEM,
                        f"Batch processing error: {exc}",
                        exception=str(exc),
                    )

    async def _collect_batch(self) -> List[BatchRequest]:
        """Collect a batch of requests based on size and timeout constraints."""
        batch: List[BatchRequest] = []
        batch_start_time = time.time()

        target_size = (
            self._get_adaptive_batch_size()
            if self.adaptive_batching
            else self.batch_size
        )

        while len(batch) < target_size:
            remaining_timeout = self.batch_timeout - (time.time() - batch_start_time)

            if remaining_timeout <= 0:
                break

            try:
                if self.priority_enabled:
                    request = await self._get_priority_request(remaining_timeout)
                else:
                    request = await asyncio.wait_for(
                        self._request_queue.get(), timeout=remaining_timeout
                    )

                if request:
                    batch.append(request)

            except asyncio.TimeoutError:
                break

        return batch

    async def _get_priority_request(self, timeout: float) -> Optional[BatchRequest]:
        """Get the highest priority request available."""
        for priority in reversed(list(Priority)):
            if self._priority_queues[priority]:
                request = self._priority_queues[priority].pop(0)
                try:
                    self._request_queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                return request

        try:
            return await asyncio.wait_for(self._request_queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    def _get_adaptive_batch_size(self) -> int:
        """Calculate adaptive batch size based on recent load patterns."""
        if not self._load_history:
            return self.batch_size

        avg_load = sum(self._load_history) / len(self._load_history)

        if avg_load > 0.8:
            target_size = min(self._max_batch_size, int(self.batch_size * 1.5))
        elif avg_load < 0.3:
            target_size = max(self._min_batch_size, int(self.batch_size * 0.7))
        else:
            target_size = self.batch_size

        return target_size

    def _update_load_history(self, load: float) -> None:
        """Update load history for adaptive batching."""
        self._load_history.append(load)

        if len(self._load_history) > self._load_window_size:
            self._load_history.pop(0)

    async def _process_batch(self, batch: List[BatchRequest]) -> None:
        """Process a batch of requests through the workflow pipeline."""
        start_time = time.time()

        current_time = time.time()
        wait_times = [current_time - req.timestamp for req in batch]

        if "logging" in self.resources:
            await self.resources["logging"].log(
                LogLevel.DEBUG,
                LogCategory.SYSTEM,
                f"Processing batch of {len(batch)} requests",
                batch_size=len(batch),
                avg_wait_time=sum(wait_times) / len(wait_times) if wait_times else 0,
            )

        tasks = []
        for request in batch:
            task = asyncio.create_task(self._process_request(request))
            tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions=True)

        processing_time = time.time() - start_time
        self._metrics.update_batch_metrics(len(batch), processing_time, wait_times)
        self._last_batch_time = time.time()

    async def _process_request(self, request: BatchRequest) -> None:
        """Process an individual request within a batch."""
        try:
            result = await super().execute(request.message, request.user_id)

            if not request.future.done():
                request.future.set_result(result)

        except Exception as exc:
            if not request.future.done():
                request.future.set_exception(exc)

    async def _flush_remaining_requests(self) -> None:
        """Process any remaining requests in the queue during shutdown."""
        remaining_requests = []

        while not self._request_queue.empty():
            try:
                request = self._request_queue.get_nowait()
                remaining_requests.append(request)
            except asyncio.QueueEmpty:
                break

        for priority_queue in self._priority_queues.values():
            remaining_requests.extend(priority_queue)
            priority_queue.clear()

        if remaining_requests:
            await self._process_batch(remaining_requests)

    def get_batch_metrics(self) -> Dict[str, Any]:
        """Get current batch processing metrics.

        Returns:
            Dictionary containing batch processing statistics
        """
        return {
            "total_batches_processed": self._metrics.total_batches_processed,
            "total_requests_processed": self._metrics.total_requests_processed,
            "avg_batch_size": round(self._metrics.avg_batch_size, 2),
            "avg_batch_processing_time": round(
                self._metrics.avg_batch_processing_time, 4
            ),
            "avg_request_wait_time": round(self._metrics.avg_request_wait_time, 4),
            "timeouts": self._metrics.timeouts,
            "priority_distribution": {
                priority.name: count
                for priority, count in self._metrics.priority_distribution.items()
            },
            "queue_size": self._request_queue.qsize(),
            "adaptive_batch_size": (
                self._get_adaptive_batch_size() if self.adaptive_batching else None
            ),
            "current_load": self._load_history[-1] if self._load_history else 0.0,
        }

    def reset_batch_metrics(self) -> None:
        """Reset batch processing metrics."""
        self._metrics = BatchMetrics()
        self._load_history.clear()

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_batch_processing()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop_batch_processing()
