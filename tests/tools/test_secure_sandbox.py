"""Tests for secure sandbox execution."""

import time
from unittest.mock import MagicMock, patch

import pytest

from entity.tools.secure_sandbox import (
    DOCKER_AVAILABLE,
    IsolationLevel,
    NetworkMode,
    ResourceMonitor,
    SandboxConfig,
    SandboxedToolRunner,
    SandboxResult,
    SecureSandboxRunner,
)


class TestSandboxConfig:
    """Test SandboxConfig configuration."""

    def test_default_config(self):
        """Test default sandbox configuration."""
        config = SandboxConfig()
        assert config.isolation_level == IsolationLevel.STRICT
        assert config.network_mode == NetworkMode.NONE
        assert config.timeout == 5.0
        assert config.memory_mb == 100
        assert config.read_only_filesystem is True
        assert config.enable_audit_log is True

    def test_custom_config(self):
        """Test custom sandbox configuration."""
        config = SandboxConfig(
            isolation_level=IsolationLevel.PARANOID,
            network_mode=NetworkMode.INTERNAL,
            timeout=10.0,
            memory_mb=256,
        )
        assert config.isolation_level == IsolationLevel.PARANOID
        assert config.network_mode == NetworkMode.INTERNAL
        assert config.timeout == 10.0
        assert config.memory_mb == 256

    def test_blocked_syscalls(self):
        """Test default blocked syscalls."""
        config = SandboxConfig()
        assert "execve" in config.blocked_syscalls
        assert "mount" in config.blocked_syscalls
        assert "ptrace" in config.blocked_syscalls


class TestSecureSandboxRunner:
    """Test SecureSandboxRunner functionality."""

    @pytest.fixture
    def basic_sandbox(self):
        """Create sandbox with basic isolation."""
        config = SandboxConfig(isolation_level=IsolationLevel.BASIC)
        return SecureSandboxRunner(config)

    @pytest.fixture
    def moderate_sandbox(self):
        """Create sandbox with moderate isolation."""
        config = SandboxConfig(isolation_level=IsolationLevel.MODERATE)
        return SecureSandboxRunner(config)

    @pytest.mark.asyncio
    async def test_basic_isolation_success(self, basic_sandbox):
        """Test successful execution with basic isolation."""

        def add(a, b):
            return a + b

        result = await basic_sandbox.run(add, 2, 3)
        assert result.success is True
        assert result.result == 5
        assert result.error is None
        assert result.execution_time > 0

    @pytest.mark.asyncio
    async def test_basic_isolation_timeout(self, basic_sandbox):
        """Test timeout handling with basic isolation."""
        basic_sandbox.config.timeout = 0.1

        def slow_function():
            time.sleep(1)
            return "done"

        result = await basic_sandbox.run(slow_function)
        assert result.success is False
        assert result.error is not None
        assert "timeout" in result.error.lower() or "timed out" in result.error.lower()

    @pytest.mark.asyncio
    async def test_basic_isolation_exception(self, basic_sandbox):
        """Test exception handling with basic isolation."""

        def failing_function():
            raise ValueError("Test error")

        result = await basic_sandbox.run(failing_function)
        assert result.success is False
        assert "Test error" in result.error
        assert result.result is None

    @pytest.mark.asyncio
    async def test_no_isolation(self):
        """Test execution with no isolation (dangerous mode)."""
        config = SandboxConfig(isolation_level=IsolationLevel.NONE)
        sandbox = SecureSandboxRunner(config)

        def get_value():
            return "no_isolation"

        result = await sandbox.run(get_value)
        assert result.success is True
        assert result.result == "no_isolation"
        # Check audit log has warning
        audit_logs = result.audit_log
        warnings = [log for log in audit_logs if log["severity"] == "WARNING"]
        assert len(warnings) > 0

    @pytest.mark.asyncio
    async def test_audit_logging(self, basic_sandbox):
        """Test security audit logging."""

        def simple_func():
            return "test"

        result = await basic_sandbox.run(simple_func)
        assert result.success is True
        assert len(result.audit_log) > 0

        # Check for start and completion entries
        log_messages = [log["message"] for log in result.audit_log]
        assert "Starting sandbox execution" in log_messages
        assert "Sandbox execution completed" in log_messages

    @pytest.mark.asyncio
    async def test_audit_logging_disabled(self):
        """Test with audit logging disabled."""
        config = SandboxConfig(
            isolation_level=IsolationLevel.BASIC, enable_audit_log=False
        )
        sandbox = SecureSandboxRunner(config)

        def simple_func():
            return "test"

        result = await sandbox.run(simple_func)
        assert result.success is True
        assert len(result.audit_log) == 0

    def test_security_report(self, basic_sandbox):
        """Test security report generation."""
        report = basic_sandbox.get_security_report()
        assert "total_executions" in report
        assert "failed_executions" in report
        assert "warnings" in report
        assert "isolation_levels_used" in report
        assert "audit_log" in report

    @pytest.mark.asyncio
    async def test_resource_limits(self, basic_sandbox):
        """Test resource limit application."""
        basic_sandbox.config.memory_mb = 50

        def memory_intensive():
            # Try to allocate large list
            try:
                data = [0] * (100 * 1024 * 1024)  # Try to allocate ~400MB
                return len(data)
            except MemoryError:
                return "memory_limited"

        result = await basic_sandbox.run(memory_intensive)
        # Result depends on system configuration
        assert result.success is True or (
            result.success is False and "memory" in result.error.lower()
        )

    @pytest.mark.skipif(not DOCKER_AVAILABLE, reason="Docker not available")
    @pytest.mark.asyncio
    async def test_docker_isolation(self):
        """Test Docker container isolation."""
        config = SandboxConfig(isolation_level=IsolationLevel.STRICT)
        sandbox = SecureSandboxRunner(config)

        def isolated_func():
            return "docker_isolated"

        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_container = MagicMock()
            mock_container.wait.return_value = {"StatusCode": 0}
            mock_container.logs.return_value = b"docker_isolated"
            mock_client.containers.create.return_value = mock_container
            mock_docker.return_value = mock_client

            _ = await sandbox.run(isolated_func)
            # Due to pickle/serialization in mock, this might not work perfectly
            # but we can check the execution flow
            assert mock_client.containers.create.called

    @pytest.mark.asyncio
    async def test_network_isolation_modes(self):
        """Test different network isolation modes."""
        for network_mode in NetworkMode:
            config = SandboxConfig(
                isolation_level=IsolationLevel.BASIC, network_mode=network_mode
            )
            sandbox = SecureSandboxRunner(config)

            def network_test():
                return f"network_{network_mode.value}"

            result = await sandbox.run(network_test)
            assert result.success is True
            assert network_mode.value in result.result


class TestResourceMonitor:
    """Test ResourceMonitor functionality."""

    def test_resource_monitor_basic(self):
        """Test basic resource monitoring."""
        monitor = ResourceMonitor()
        monitor.start()
        time.sleep(0.1)
        stats = monitor.stop()

        assert "duration" in stats
        assert stats["duration"] > 0

    def test_resource_monitor_without_psutil(self):
        """Test resource monitoring without psutil available."""
        monitor = ResourceMonitor()
        monitor.start()
        stats = monitor.stop()

        # Should have basic stats even without psutil
        assert "duration" in stats
        assert stats["duration"] > 0
        # May have monitoring_available=False or monitoring_error=True
        if "monitoring_available" in stats:
            assert stats["monitoring_available"] is False
        elif "monitoring_error" in stats:
            assert stats["monitoring_error"] is True


class TestBackwardCompatibility:
    """Test backward compatibility with existing SandboxedToolRunner."""

    @pytest.mark.asyncio
    async def test_sandboxed_tool_runner_compatibility(self):
        """Test that SandboxedToolRunner maintains backward compatibility."""
        runner = SandboxedToolRunner(timeout=2.0, memory_mb=64)
        assert runner.config.timeout == 2.0
        assert runner.config.memory_mb == 64
        assert runner.config.isolation_level == IsolationLevel.BASIC

        def compatible_func(x):
            return x * 2

        result = await runner.run(compatible_func, 5)
        assert result.success is True
        assert result.result == 10


class TestIsolationLevels:
    """Test different isolation levels."""

    @pytest.mark.asyncio
    async def test_all_isolation_levels(self):
        """Test execution with all isolation levels."""
        test_levels = [
            IsolationLevel.NONE,
            IsolationLevel.BASIC,
            # Skip MODERATE and above as they require subprocess/docker
        ]

        for level in test_levels:
            config = SandboxConfig(isolation_level=level)
            sandbox = SecureSandboxRunner(config)

            def test_func(level_name):
                return f"executed_{level_name}"

            result = await sandbox.run(test_func, level.value)
            assert result.success is True
            assert level.value in result.result

    @pytest.mark.asyncio
    async def test_paranoid_mode(self):
        """Test paranoid isolation mode configuration."""
        config = SandboxConfig(isolation_level=IsolationLevel.PARANOID)

        # Should have strictest settings
        assert config.network_mode == NetworkMode.NONE
        assert config.read_only_filesystem is True
        assert len(config.blocked_syscalls) > 0

        # Test sandbox initialization with paranoid config
        sandbox = SecureSandboxRunner(config)

        # If Docker not available, paranoid mode still configures but doesn't enforce
        # It will fallback during execution, not during initialization
        assert sandbox.config.isolation_level in [
            IsolationLevel.PARANOID,
            IsolationLevel.MODERATE,
        ]


class TestSandboxResult:
    """Test SandboxResult data structure."""

    def test_successful_result(self):
        """Test successful execution result."""
        result = SandboxResult(
            success=True,
            result="test_output",
            execution_time=1.5,
            memory_used_mb=50.0,
        )
        assert result.success is True
        assert result.result == "test_output"
        assert result.error is None
        assert result.execution_time == 1.5
        assert result.memory_used_mb == 50.0

    def test_failed_result(self):
        """Test failed execution result."""
        result = SandboxResult(
            success=False,
            result=None,
            error="Test error message",
            execution_time=0.5,
        )
        assert result.success is False
        assert result.result is None
        assert result.error == "Test error message"
        assert result.execution_time == 0.5


class TestSecurityFeatures:
    """Test security-specific features."""

    def test_syscall_blocking(self):
        """Test syscall blocking configuration."""
        config = SandboxConfig()
        dangerous_syscalls = ["execve", "fork", "mount", "ptrace"]
        for syscall in dangerous_syscalls:
            assert syscall in config.blocked_syscalls

    def test_filesystem_isolation(self):
        """Test filesystem isolation settings."""
        config = SandboxConfig()
        assert config.read_only_filesystem is True
        assert len(config.allowed_paths) == 0  # No paths allowed by default

    def test_process_limits(self):
        """Test process limit configuration."""
        config = SandboxConfig()
        assert config.max_processes == 10
        assert config.cpu_shares == 512

    @pytest.mark.asyncio
    async def test_security_audit_entry(self):
        """Test security audit entry creation."""
        config = SandboxConfig(isolation_level=IsolationLevel.BASIC)
        sandbox = SecureSandboxRunner(config)

        def test_func():
            return "audit_test"

        result = await sandbox.run(test_func)
        assert result.success is True

        # Check audit entries have required fields
        for entry in result.audit_log:
            assert "timestamp" in entry
            assert "event_type" in entry
            assert "severity" in entry
            assert "message" in entry
            assert "details" in entry
