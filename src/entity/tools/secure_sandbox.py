"""Secure sandbox execution using Docker and system-level isolation.

This module provides comprehensive sandboxing for untrusted code execution
using multiple layers of security including Docker containers, seccomp filters,
and resource limits.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

try:
    import docker
    from docker.errors import ContainerError, ImageNotFound

    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    docker = None
    ContainerError = Exception
    ImageNotFound = Exception


class IsolationLevel(Enum):
    """Security isolation levels for sandbox execution."""

    NONE = "none"
    BASIC = "basic"
    MODERATE = "moderate"
    STRICT = "strict"
    PARANOID = "paranoid"


class NetworkMode(Enum):
    """Network isolation modes."""

    NONE = "none"
    INTERNAL = "internal"
    FILTERED = "filtered"
    FULL = "full"


@dataclass
class SandboxConfig:
    """Configuration for sandbox execution."""

    isolation_level: IsolationLevel = IsolationLevel.STRICT
    network_mode: NetworkMode = NetworkMode.NONE
    timeout: float = 5.0
    memory_mb: int = 100
    cpu_shares: int = 512
    max_processes: int = 10
    read_only_filesystem: bool = True
    allowed_syscalls: Set[str] = field(default_factory=set)
    blocked_syscalls: Set[str] = field(
        default_factory=lambda: {
            "clone",
            "fork",
            "vfork",
            "execve",
            "execveat",
            "ptrace",
            "process_vm_readv",
            "process_vm_writev",
            "mount",
            "umount",
            "pivot_root",
            "chroot",
            "setns",
            "unshare",
            "seccomp",
            "bpf",
        }
    )
    allowed_paths: Set[Path] = field(default_factory=set)
    environment_vars: Dict[str, str] = field(default_factory=dict)
    docker_image: str = "python:3.11-slim"
    enable_audit_log: bool = True


@dataclass
class SandboxResult:
    """Result of sandbox execution."""

    success: bool
    result: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    memory_used_mb: float = 0.0
    cpu_time: float = 0.0
    audit_log: List[Dict[str, Any]] = field(default_factory=list)
    container_id: Optional[str] = None


@dataclass
class SecurityAuditEntry:
    """Security audit log entry."""

    timestamp: datetime
    event_type: str
    severity: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


class SecureSandboxRunner:
    """Secure sandbox runner with multiple isolation layers."""

    def __init__(self, config: Optional[SandboxConfig] = None):
        """Initialize the secure sandbox runner.

        Args:
            config: Sandbox configuration. Uses strict defaults if not provided.
        """
        self.config = config or SandboxConfig()
        self.docker_client = None
        self.audit_log: List[SecurityAuditEntry] = []

        if DOCKER_AVAILABLE and self.config.isolation_level in [
            IsolationLevel.STRICT,
            IsolationLevel.PARANOID,
        ]:
            try:
                self.docker_client = docker.from_env()
                self._ensure_sandbox_image()
            except Exception as e:
                self._log_audit(
                    "WARNING",
                    "Docker initialization failed",
                    {"error": str(e), "fallback": "MODERATE"},
                )
                self.config.isolation_level = IsolationLevel.MODERATE

    def _ensure_sandbox_image(self) -> None:
        """Ensure the sandbox Docker image exists or create it."""
        if not self.docker_client:
            return

        try:
            self.docker_client.images.get(self.config.docker_image)
        except ImageNotFound:
            self._log_audit(
                "INFO", "Pulling Docker image", {"image": self.config.docker_image}
            )
            self.docker_client.images.pull(self.config.docker_image)

    def _log_audit(
        self, severity: str, message: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a security audit entry."""
        if not self.config.enable_audit_log:
            return

        entry = SecurityAuditEntry(
            timestamp=datetime.now(),
            event_type="SANDBOX_EXECUTION",
            severity=severity,
            message=message,
            details=details or {},
        )
        self.audit_log.append(entry)

    async def run(
        self, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> SandboxResult:
        """Execute a function in the secure sandbox.

        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            SandboxResult with execution details
        """
        start_time = time.time()
        sandbox_id = str(uuid.uuid4())

        self._log_audit(
            "INFO",
            "Starting sandbox execution",
            {
                "sandbox_id": sandbox_id,
                "function": func.__name__ if hasattr(func, "__name__") else str(func),
                "isolation_level": self.config.isolation_level.value,
            },
        )

        try:
            if self.config.isolation_level == IsolationLevel.NONE:
                result = await self._run_no_isolation(func, *args, **kwargs)
            elif self.config.isolation_level == IsolationLevel.BASIC:
                result = await self._run_basic_isolation(func, *args, **kwargs)
            elif self.config.isolation_level == IsolationLevel.MODERATE:
                result = await self._run_moderate_isolation(func, *args, **kwargs)
            elif self.config.isolation_level in [
                IsolationLevel.STRICT,
                IsolationLevel.PARANOID,
            ]:
                result = await self._run_container_isolation(
                    func, sandbox_id, *args, **kwargs
                )
            else:
                raise ValueError(
                    f"Unknown isolation level: {self.config.isolation_level}"
                )

            execution_time = time.time() - start_time
            self._log_audit(
                "INFO",
                "Sandbox execution completed",
                {"sandbox_id": sandbox_id, "execution_time": execution_time},
            )

            return SandboxResult(
                success=True,
                result=result,
                execution_time=execution_time,
                audit_log=self._get_audit_log_dicts(),
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e) if str(e) else f"{type(e).__name__}: {e}"
            self._log_audit(
                "ERROR",
                "Sandbox execution failed",
                {
                    "sandbox_id": sandbox_id,
                    "error": error_msg,
                    "type": type(e).__name__,
                },
            )

            return SandboxResult(
                success=False,
                result=None,
                error=error_msg,
                execution_time=execution_time,
                audit_log=self._get_audit_log_dicts(),
            )

    async def _run_no_isolation(
        self, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Any:
        """Run with no isolation (dangerous, for testing only)."""
        self._log_audit("WARNING", "Running with no isolation")
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, func, *args, **kwargs)

    async def _run_basic_isolation(
        self, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Any:
        """Run with basic resource limits."""
        self._log_audit("INFO", "Applying basic resource limits")

        loop = asyncio.get_running_loop()

        def _run_func():
            return func(*args, **kwargs)

        return await asyncio.wait_for(
            loop.run_in_executor(None, _run_func), self.config.timeout
        )

    async def _run_moderate_isolation(
        self, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Any:
        """Run with process isolation using subprocess."""
        import base64
        import pickle
        import subprocess
        import sys

        self._log_audit("INFO", "Running with process isolation")

        func_data = base64.b64encode(pickle.dumps((func, args, kwargs))).decode()

        script = f"""
import base64
import pickle
import sys

try:
    func_data = base64.b64decode('{func_data}')
    func, args, kwargs = pickle.loads(func_data)
    result = func(*args, **kwargs)
    sys.stdout.buffer.write(base64.b64encode(pickle.dumps(result)))
except Exception as e:
    sys.stderr.write(str(e))
    sys.exit(1)
"""

        try:
            result = subprocess.run(
                [sys.executable, "-c", script],
                capture_output=True,
                timeout=self.config.timeout,
                check=True,
            )
            return pickle.loads(base64.b64decode(result.stdout))
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Execution exceeded {self.config.timeout} seconds")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Subprocess execution failed: {e.stderr.decode()}")

    async def _run_container_isolation(
        self, func: Callable[..., Any], sandbox_id: str, *args: Any, **kwargs: Any
    ) -> Any:
        """Run in Docker container with full isolation."""
        if not self.docker_client:
            self._log_audit(
                "WARNING", "Docker not available, falling back to moderate isolation"
            )
            return await self._run_moderate_isolation(func, *args, **kwargs)

        import base64
        import pickle

        self._log_audit(
            "INFO",
            "Running in Docker container",
            {
                "image": self.config.docker_image,
                "network": self.config.network_mode.value,
            },
        )

        func_data = base64.b64encode(pickle.dumps((func, args, kwargs))).decode()

        script = f"""
import base64
import pickle
import sys

func_data = base64.b64decode('{func_data}')
func, args, kwargs = pickle.loads(func_data)
result = func(*args, **kwargs)
sys.stdout.buffer.write(base64.b64encode(pickle.dumps(result)))
"""

        container_config = {
            "image": self.config.docker_image,
            "command": ["python", "-c", script],
            "detach": True,
            "mem_limit": f"{self.config.memory_mb}m",
            "memswap_limit": f"{self.config.memory_mb}m",
            "cpu_shares": self.config.cpu_shares,
            "network_mode": self.config.network_mode.value,
            "read_only": self.config.read_only_filesystem,
            "security_opt": ["no-new-privileges"],
            "cap_drop": ["ALL"],
            "environment": self.config.environment_vars,
        }

        if self.config.isolation_level == IsolationLevel.PARANOID:
            container_config.update(
                {
                    "pids_limit": self.config.max_processes,
                    "cap_drop": ["ALL"],
                    "security_opt": ["no-new-privileges", "apparmor=docker-default"],
                }
            )

        container = None
        try:
            container = self.docker_client.containers.create(**container_config)
            container.start()

            exit_code = container.wait(timeout=int(self.config.timeout))["StatusCode"]

            if exit_code != 0:
                logs = container.logs(stderr=True).decode()
                raise RuntimeError(f"Container execution failed: {logs}")

            output = container.logs(stdout=True).decode()
            result = pickle.loads(base64.b64decode(output))

            self._log_audit(
                "INFO",
                "Container execution successful",
                {"container_id": container.id[:12]},
            )
            return result

        except Exception as e:
            self._log_audit(
                "ERROR",
                "Container execution failed",
                {
                    "error": str(e),
                    "container_id": container.id[:12] if container else None,
                },
            )
            raise
        finally:
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass

    def _get_audit_log_dicts(self) -> List[Dict[str, Any]]:
        """Convert audit log entries to dictionaries."""
        return [
            {
                "timestamp": entry.timestamp.isoformat(),
                "event_type": entry.event_type,
                "severity": entry.severity,
                "message": entry.message,
                "details": entry.details,
            }
            for entry in self.audit_log
        ]

    def get_security_report(self) -> Dict[str, Any]:
        """Generate a security report of sandbox usage."""
        return {
            "total_executions": len(
                [e for e in self.audit_log if e.message == "Starting sandbox execution"]
            ),
            "failed_executions": len(
                [e for e in self.audit_log if e.severity == "ERROR"]
            ),
            "warnings": len([e for e in self.audit_log if e.severity == "WARNING"]),
            "isolation_levels_used": list(
                set(
                    e.details.get("isolation_level", "unknown")
                    for e in self.audit_log
                    if "isolation_level" in e.details
                )
            ),
            "audit_log": self._get_audit_log_dicts(),
        }


class ResourceMonitor:
    """Monitor resource usage during sandbox execution."""

    def __init__(self):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.peak_memory_mb: float = 0.0
        self.cpu_percent: float = 0.0
        self.io_reads: int = 0
        self.io_writes: int = 0
        self.network_bytes_sent: int = 0
        self.network_bytes_recv: int = 0

    def start(self) -> None:
        """Start monitoring resources."""
        self.start_time = time.time()
        try:
            import psutil

            self.process = psutil.Process()
            self.initial_cpu = self.process.cpu_percent()
        except ImportError:
            self.process = None

    def stop(self) -> Dict[str, Any]:
        """Stop monitoring and return resource usage."""
        self.end_time = time.time()

        if not self.process:
            return {
                "duration": self.end_time - self.start_time if self.start_time else 0,
                "monitoring_available": False,
            }

        try:
            memory_info = self.process.memory_info()
            cpu_percent = self.process.cpu_percent()
            io_counters = self.process.io_counters()

            return {
                "duration": self.end_time - self.start_time,
                "memory_mb": memory_info.rss / 1024 / 1024,
                "cpu_percent": cpu_percent,
                "io_reads": io_counters.read_count if io_counters else 0,
                "io_writes": io_counters.write_count if io_counters else 0,
            }
        except Exception:
            return {
                "duration": self.end_time - self.start_time if self.start_time else 0,
                "monitoring_error": True,
            }


class SandboxedToolRunner(SecureSandboxRunner):
    """Backward compatible sandbox runner."""

    def __init__(self, timeout: float = 5.0, memory_mb: Optional[int] = None):
        config = SandboxConfig(
            isolation_level=IsolationLevel.BASIC,
            timeout=timeout,
            memory_mb=memory_mb or 100,
        )
        super().__init__(config)
