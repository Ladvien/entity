import asyncio
import functools
import inspect
import resource
from typing import Any, Callable, Optional


class SandboxedToolRunner:
    """Run tools with timeout and optional resource limits."""

    def __init__(self, timeout: float = 5.0, memory_mb: Optional[int] = None) -> None:
        self.timeout = timeout
        self.memory_bytes = None if memory_mb is None else memory_mb * 1024 * 1024

    async def run(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        loop = asyncio.get_running_loop()
        bound = functools.partial(self._run_with_limits, func, *args, **kwargs)
        return await asyncio.wait_for(loop.run_in_executor(None, bound), self.timeout)

    def _run_with_limits(
        self, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Any:
        if self.memory_bytes is not None:
            try:
                resource.setrlimit(
                    resource.RLIMIT_AS, (self.memory_bytes, self.memory_bytes)
                )
            except ValueError:
                pass
        try:
            resource.setrlimit(
                resource.RLIMIT_CPU, (int(self.timeout), int(self.timeout))
            )
        except ValueError:
            pass
        result = func(*args, **kwargs)
        if inspect.iscoroutine(result):
            return asyncio.run(asyncio.wait_for(result, self.timeout))
        return result
