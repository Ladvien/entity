"""Legacy sandbox module for backward compatibility.

This module maintains the original SandboxedToolRunner interface
while using the new secure sandbox implementation underneath.
"""

from typing import Any, Callable, Optional

from entity.tools.secure_sandbox import (
    IsolationLevel,
    SandboxConfig,
    SecureSandboxRunner,
)


class SandboxedToolRunner:
    """Run tools with timeout and optional resource limits.

    This is a compatibility wrapper around SecureSandboxRunner.
    For new code, use SecureSandboxRunner directly for better security.
    """

    def __init__(self, timeout: float = 5.0, memory_mb: Optional[int] = None) -> None:
        """Initialize sandbox with basic isolation for backward compatibility.

        Args:
            timeout: Maximum execution time in seconds
            memory_mb: Memory limit in megabytes
        """
        config = SandboxConfig(
            isolation_level=IsolationLevel.BASIC,
            timeout=timeout,
            memory_mb=memory_mb or 100,
        )
        self._runner = SecureSandboxRunner(config)
        self.timeout = timeout
        self.memory_bytes = None if memory_mb is None else memory_mb * 1024 * 1024

    async def run(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Run function in sandbox with resource limits.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            TimeoutError: If execution exceeds timeout
            Exception: Any exception raised by the function
        """
        result = await self._runner.run(func, *args, **kwargs)
        if result.success:
            return result.result
        else:
            raise Exception(result.error)
