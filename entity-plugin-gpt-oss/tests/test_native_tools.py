"""Unit tests for Native Tool Orchestrator Plugin."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from entity.plugins.context import PluginContext
from entity.workflow.executor import WorkflowExecutor

from entity_plugin_gpt_oss.native_tools import (
    BrowserTool,
    GPTOSSToolOrchestrator,
    PythonTool,
    RateLimiter,
    ToolChain,
    ToolConfig,
    ToolExecutionMode,
    ToolInvocation,
    ToolResult,
    ToolStatus,
    ToolType,
)


class TestGPTOSSToolOrchestrator:
    """Test GPTOSSToolOrchestrator functionality."""

    @pytest.fixture
    def mock_resources(self):
        """Create mock resources for testing."""
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(return_value="Test response")

        class MockMemory:
            def __init__(self):
                self.data = {}

            async def store(self, key, value):
                self.data[key] = value

            async def load(self, key, default=None):
                return self.data.get(key, default)

        mock_sandbox = MagicMock()
        mock_sandbox.run = AsyncMock(return_value={"success": True})
        mock_sandbox.context_id = "test_context"

        mock_logging = MagicMock()
        mock_logging.log = AsyncMock()

        return {
            "llm": mock_llm,
            "memory": MockMemory(),
            "sandbox": mock_sandbox,
            "logging": mock_logging,
        }

    @pytest.fixture
    def basic_plugin(self, mock_resources):
        """Create basic plugin with default config."""
        config = {
            "enable_browser_tool": True,
            "enable_python_tool": True,
            "enable_tool_chaining": True,
            "log_tool_invocations": True,
        }
        return GPTOSSToolOrchestrator(mock_resources, config)

    @pytest.fixture
    def restricted_plugin(self, mock_resources):
        """Create plugin with restricted config."""
        config = {
            "enable_browser_tool": False,
            "enable_python_tool": True,
            "enable_tool_chaining": False,
            "require_user_approval": True,
            "default_execution_mode": ToolExecutionMode.RESTRICTED.value,
        }
        return GPTOSSToolOrchestrator(mock_resources, config)

    @pytest.fixture
    def context(self, mock_resources):
        """Create mock plugin context."""
        ctx = PluginContext(mock_resources, "test_user")
        ctx.current_stage = WorkflowExecutor.DO
        ctx.message = "Test message"
        ctx.execution_id = "test_exec_123"
        ctx.remember = AsyncMock()
        ctx.recall = AsyncMock(return_value=None)
        ctx.log = AsyncMock()
        ctx.get_resource = lambda name: mock_resources.get(name)
        return ctx

    def test_plugin_initialization(self, basic_plugin):
        """Test plugin initialization."""
        assert basic_plugin.config.enable_browser_tool is True
        assert basic_plugin.config.enable_python_tool is True
        assert WorkflowExecutor.DO in basic_plugin.supported_stages
        assert "sandbox" in basic_plugin.dependencies
        assert "browser" in basic_plugin.tools
        assert "python" in basic_plugin.tools

    def test_plugin_initialization_invalid_config(self, mock_resources):
        """Test plugin initialization with invalid config."""
        config = {"max_chain_length": -1}  # Invalid negative value

        with pytest.raises(ValueError, match="Invalid configuration"):
            GPTOSSToolOrchestrator(mock_resources, config)

    def test_plugin_with_disabled_tools(self, mock_resources):
        """Test plugin with tools disabled."""
        config = {
            "enable_browser_tool": False,
            "enable_python_tool": False,
        }
        plugin = GPTOSSToolOrchestrator(mock_resources, config)

        assert len(plugin.tools) == 0
        assert plugin.get_available_tools() == []

    @pytest.mark.asyncio
    async def test_basic_execution_no_tools(self, basic_plugin, context):
        """Test execution with no tool invocations."""
        context.message = "Simple message without tools"
        result = await basic_plugin._execute_impl(context)

        assert result == "Simple message without tools"
        context.log.assert_not_called()

    @pytest.mark.asyncio
    async def test_parse_tool_invocations_single(self, basic_plugin):
        """Test parsing single tool invocation."""
        message = '<tool:browser>{"action": "search", "query": "test"}</tool>'
        invocations = await basic_plugin._parse_tool_invocations(message)

        assert len(invocations) == 1
        assert invocations[0].tool_name == "browser"
        assert invocations[0].parameters == {"action": "search", "query": "test"}

    @pytest.mark.asyncio
    async def test_parse_tool_invocations_multiple(self, basic_plugin):
        """Test parsing multiple tool invocations."""
        message = """
        <tool:browser>{"action": "search", "query": "test"}</tool>
        <tool:python>{"code": "print('hello')"}</tool>
        """
        invocations = await basic_plugin._parse_tool_invocations(message)

        assert len(invocations) == 2
        assert invocations[0].tool_name == "browser"
        assert invocations[1].tool_name == "python"

    @pytest.mark.asyncio
    async def test_parse_tool_invocations_simple_format(self, basic_plugin):
        """Test parsing simple parameter format."""
        message = """<tool:browser>
        action: search
        query: test query
        </tool>"""
        invocations = await basic_plugin._parse_tool_invocations(message)

        assert len(invocations) == 1
        assert invocations[0].parameters["action"] == "search"
        assert invocations[0].parameters["query"] == "test query"

    @pytest.mark.asyncio
    async def test_execute_single_browser_tool(self, basic_plugin, context):
        """Test executing browser tool."""
        context.message = '<tool:browser>{"action": "search", "query": "test"}</tool>'
        result = await basic_plugin._execute_impl(context)

        assert "[browser]:" in result
        assert "test" in result
        context.log.assert_called()

    @pytest.mark.asyncio
    async def test_execute_single_python_tool(self, basic_plugin, context):
        """Test executing Python tool."""
        context.message = '<tool:python>{"code": "print(2 + 2)"}</tool>'
        result = await basic_plugin._execute_impl(context)

        assert "[python]:" in result
        context.log.assert_called()

    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self, basic_plugin, context):
        """Test executing unknown tool."""
        invocation = ToolInvocation(
            tool_name="unknown",
            parameters={},
            correlation_id="test_123",
        )
        result = await basic_plugin._execute_single_tool(context, invocation)

        assert result.status == ToolStatus.FAILED
        assert "Unknown tool" in result.error

    @pytest.mark.asyncio
    async def test_tool_chaining(self, basic_plugin, context):
        """Test tool chaining execution."""
        context.message = """
        <tool:browser>{"action": "search", "query": "python"}</tool>
        <tool:python>{"code": "print('found')"}</tool>
        """
        result = await basic_plugin._execute_impl(context)

        assert "[browser]:" in result
        assert "[python]:" in result

    @pytest.mark.asyncio
    async def test_tool_chaining_disabled(self, restricted_plugin, context):
        """Test with tool chaining disabled."""
        context.message = """
        <tool:python>{"code": "print('first')"}</tool>
        <tool:python>{"code": "print('second')"}</tool>
        """
        result = await restricted_plugin._execute_impl(context)

        # Should only execute first tool when chaining disabled
        assert result.count("[python]:") == 1

    @pytest.mark.asyncio
    async def test_max_chain_length(self, basic_plugin, context):
        """Test max chain length enforcement."""
        basic_plugin.config.max_chain_length = 2

        # Create chain longer than limit
        invocations = [
            ToolInvocation(
                tool_name="python",
                parameters={"code": f"print({i})"},
                correlation_id=f"test_{i}",
            )
            for i in range(3)
        ]

        with pytest.raises(ValueError, match="Tool chain too long"):
            await basic_plugin._execute_tool_chain(context, invocations)

    @pytest.mark.asyncio
    async def test_global_rate_limiting(self, basic_plugin, context):
        """Test global rate limiting."""
        # Set very low rate limit
        basic_plugin.global_rate_limiter = RateLimiter(1)

        invocation = ToolInvocation(
            tool_name="browser",
            parameters={"action": "search", "query": "test"},
            correlation_id="test_123",
        )

        # First request should succeed
        result1 = await basic_plugin._execute_single_tool(context, invocation)
        assert result1.status == ToolStatus.COMPLETED

        # Second request should be rate limited
        result2 = await basic_plugin._execute_single_tool(context, invocation)
        assert result2.status == ToolStatus.RATE_LIMITED

    @pytest.mark.asyncio
    async def test_execution_timeout(self, basic_plugin, context):
        """Test execution timeout handling."""
        basic_plugin.config.max_total_execution_time_ms = 1  # Very short timeout

        # Mock slow execution
        with patch("time.time", side_effect=[0, 1000, 2000]):  # Simulate time passing
            invocations = [
                ToolInvocation(
                    tool_name="python",
                    parameters={"code": "print('test')"},
                    correlation_id="test_1",
                ),
                ToolInvocation(
                    tool_name="python",
                    parameters={"code": "print('test2')"},
                    correlation_id="test_2",
                ),
            ]

            results = await basic_plugin._execute_tool_chain(context, invocations)

            # Second tool should timeout
            assert results[1].status == ToolStatus.TIMEOUT

    @pytest.mark.asyncio
    async def test_store_execution_history(self, basic_plugin, context):
        """Test execution history storage."""
        invocation = ToolInvocation(
            tool_name="browser",
            parameters={"action": "search", "query": "test"},
            correlation_id="test_123",
        )
        result = ToolResult(
            tool_name="browser",
            correlation_id="test_123",
            status=ToolStatus.COMPLETED,
            result={"data": "test"},
            execution_time_ms=100,
        )

        await basic_plugin._store_execution_history(context, invocation, result)

        assert len(basic_plugin.execution_history) == 1
        context.remember.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_execution_stats(self, basic_plugin):
        """Test getting execution statistics."""
        # Add some execution history
        basic_plugin.execution_history = [
            {
                "tool_name": "browser",
                "status": "completed",
                "execution_time_ms": 100,
            },
            {
                "tool_name": "python",
                "status": "completed",
                "execution_time_ms": 200,
            },
            {
                "tool_name": "browser",
                "status": "failed",
                "execution_time_ms": 50,
            },
        ]

        stats = await basic_plugin.get_execution_stats()

        assert stats["total_executions"] == 3
        assert stats["by_tool"]["browser"] == 2
        assert stats["by_tool"]["python"] == 1
        assert stats["by_status"]["completed"] == 2
        assert stats["by_status"]["failed"] == 1
        assert stats["average_execution_time_ms"] == 350 / 3

    def test_get_available_tools(self, basic_plugin):
        """Test getting available tools."""
        tools = basic_plugin.get_available_tools()
        assert "browser" in tools
        assert "python" in tools

    def test_get_tool_config(self, basic_plugin):
        """Test getting tool configuration."""
        config = basic_plugin.get_tool_config("browser")
        assert config is not None
        assert config.tool_type == ToolType.BROWSER
        assert config.name == "browser"

        # Unknown tool
        config = basic_plugin.get_tool_config("unknown")
        assert config is None

    def test_get_harmony_tool_definitions(self, basic_plugin):
        """Test getting harmony format definitions."""
        definitions = basic_plugin.get_harmony_tool_definitions()

        assert len(definitions) == 2
        browser_def = next(d for d in definitions if d["name"] == "browser")
        assert browser_def["type"] == "tool"
        assert "description" in browser_def
        assert "parameters" in browser_def

    @pytest.mark.asyncio
    async def test_reset_rate_limits(self, basic_plugin):
        """Test resetting rate limits."""
        # Trigger rate limit
        basic_plugin.global_rate_limiter.requests = [datetime.now()] * 100

        await basic_plugin.reset_rate_limits()

        assert len(basic_plugin.global_rate_limiter.requests) == 0

    @pytest.mark.asyncio
    async def test_execute_tool_programmatically(self, basic_plugin):
        """Test programmatic tool execution."""
        result = await basic_plugin.execute_tool(
            "browser",
            {"action": "search", "query": "test"},
        )

        assert result.status == ToolStatus.COMPLETED
        assert result.tool_name == "browser"

    @pytest.mark.asyncio
    async def test_error_handling(self, basic_plugin, context):
        """Test error handling in execution."""
        # Create invalid tool invocation
        context.message = "<tool:browser>invalid json</tool>"

        result = await basic_plugin._execute_impl(context)

        # Should handle error gracefully
        assert "Tool execution failed" in result or "[browser]:" in result


class TestBrowserTool:
    """Test BrowserTool functionality."""

    @pytest.fixture
    def browser_tool(self):
        """Create browser tool instance."""
        return BrowserTool()

    @pytest.mark.asyncio
    async def test_browser_search(self, browser_tool):
        """Test browser search action."""
        result = await browser_tool.execute({"action": "search", "query": "test query"})

        assert result.status == ToolStatus.COMPLETED
        assert result.result is not None
        assert "results" in result.result
        assert len(result.result["results"]) > 0

    @pytest.mark.asyncio
    async def test_browser_navigate(self, browser_tool):
        """Test browser navigate action."""
        result = await browser_tool.execute(
            {"action": "navigate", "query": "https://example.com"}
        )

        assert result.status == ToolStatus.COMPLETED
        assert result.result is not None
        assert "url" in result.result
        assert "content" in result.result

    @pytest.mark.asyncio
    async def test_browser_extract(self, browser_tool):
        """Test browser extract action."""
        result = await browser_tool.execute(
            {
                "action": "extract",
                "query": "https://example.com",
                "extract_selector": ".main-content",
            }
        )

        assert result.status == ToolStatus.COMPLETED
        assert result.result is not None
        assert "extracted" in result.result

    @pytest.mark.asyncio
    async def test_browser_missing_query(self, browser_tool):
        """Test browser with missing query."""
        result = await browser_tool.execute({"action": "search"})

        assert result.status == ToolStatus.FAILED
        assert "Query parameter is required" in result.error

    @pytest.mark.asyncio
    async def test_browser_blocked_domain(self, browser_tool):
        """Test browser with blocked domain."""
        result = await browser_tool.execute(
            {"action": "navigate", "query": "http://localhost/test"}
        )

        assert result.status == ToolStatus.FAILED
        assert "blocked" in result.error.lower()

    @pytest.mark.asyncio
    async def test_browser_rate_limiting(self, browser_tool):
        """Test browser rate limiting."""
        # Set very low rate limit
        browser_tool.rate_limiter = RateLimiter(1)

        # First request should succeed
        result1 = await browser_tool.execute({"action": "search", "query": "test"})
        assert result1.status == ToolStatus.COMPLETED

        # Second request should be rate limited
        result2 = await browser_tool.execute({"action": "search", "query": "test"})
        assert result2.status == ToolStatus.RATE_LIMITED

    def test_browser_validate_url(self, browser_tool):
        """Test URL validation."""
        # Valid URL
        browser_tool._validate_url("https://example.com")

        # Blocked domain
        with pytest.raises(ValueError, match="blocked"):
            browser_tool._validate_url("http://localhost")

    def test_browser_harmony_format(self, browser_tool):
        """Test browser harmony format."""
        harmony = browser_tool.get_harmony_format()

        assert harmony["type"] == "tool"
        assert harmony["name"] == "browser"
        assert "description" in harmony
        assert "parameters" in harmony


class TestPythonTool:
    """Test PythonTool functionality."""

    @pytest.fixture
    def python_tool(self):
        """Create Python tool instance."""
        return PythonTool()

    @pytest.mark.asyncio
    async def test_python_execute_simple(self, python_tool):
        """Test Python code execution."""
        result = await python_tool.execute({"code": "result = 2 + 2"})

        assert result.status == ToolStatus.COMPLETED
        assert result.result is not None
        assert result.result["success"] is True

    @pytest.mark.asyncio
    async def test_python_with_imports(self, python_tool):
        """Test Python execution with imports."""
        result = await python_tool.execute(
            {
                "code": "result = 3.14",  # Simplified code that doesn't need actual import
                "imports": ["math"],
            }
        )

        assert result.status == ToolStatus.COMPLETED
        assert result.result is not None

    @pytest.mark.asyncio
    async def test_python_missing_code(self, python_tool):
        """Test Python with missing code."""
        result = await python_tool.execute({})

        assert result.status == ToolStatus.FAILED
        assert "Code parameter is required" in result.error

    @pytest.mark.asyncio
    async def test_python_blocked_import(self, python_tool):
        """Test Python with blocked import."""
        result = await python_tool.execute(
            {
                "code": "import os",
                "imports": ["os"],
            }
        )

        assert result.status == ToolStatus.FAILED
        assert "blocked" in result.error.lower()

    @pytest.mark.asyncio
    async def test_python_dangerous_code(self, python_tool):
        """Test Python with dangerous code patterns."""
        result = await python_tool.execute({"code": "__import__('os').system('ls')"})

        assert result.status == ToolStatus.FAILED
        assert "Dangerous pattern" in result.error

    @pytest.mark.asyncio
    async def test_python_rate_limiting(self, python_tool):
        """Test Python rate limiting."""
        # Set very low rate limit
        python_tool.rate_limiter = RateLimiter(1)

        # First request should succeed
        result1 = await python_tool.execute({"code": "print('test')"})
        assert result1.status == ToolStatus.COMPLETED

        # Second request should be rate limited
        result2 = await python_tool.execute({"code": "print('test2')"})
        assert result2.status == ToolStatus.RATE_LIMITED

    def test_python_validate_imports(self, python_tool):
        """Test import validation."""
        # Valid import
        python_tool._validate_imports(["math", "json"])

        # Blocked import
        with pytest.raises(ValueError, match="blocked"):
            python_tool._validate_imports(["os"])

        # Not allowed import
        with pytest.raises(ValueError, match="not in allowed"):
            python_tool._validate_imports(["numpy"])

    def test_python_validate_code_safety(self, python_tool):
        """Test code safety validation."""
        # Safe code
        python_tool._validate_code_safety("x = 2 + 2")

        # Dangerous patterns
        dangerous_codes = [
            "__import__('os')",
            "exec('print(1)')",
            "eval('2+2')",
            "open('/etc/passwd')",
            "globals()['__builtins__']",
        ]

        for code in dangerous_codes:
            with pytest.raises(ValueError, match="Dangerous pattern"):
                python_tool._validate_code_safety(code)

    def test_python_build_safe_environment(self, python_tool):
        """Test building safe execution environment."""
        env = python_tool._build_safe_environment(["math", "json"])

        assert "math" in env
        assert "json" in env
        assert "os" not in env
        assert "sys" not in env

    def test_python_harmony_format(self, python_tool):
        """Test Python harmony format."""
        harmony = python_tool.get_harmony_format()

        assert harmony["type"] == "tool"
        assert harmony["name"] == "python"
        assert "description" in harmony
        assert "parameters" in harmony


class TestRateLimiter:
    """Test RateLimiter functionality."""

    @pytest.mark.asyncio
    async def test_rate_limiter_allow(self):
        """Test rate limiter allowing requests."""
        limiter = RateLimiter(5)

        # First 5 requests should be allowed
        for _ in range(5):
            assert await limiter.allow_request() is True

        # 6th request should be denied
        assert await limiter.allow_request() is False

    @pytest.mark.asyncio
    async def test_rate_limiter_time_window(self):
        """Test rate limiter time window."""
        limiter = RateLimiter(2)

        # Add old requests (outside window)
        old_time = datetime.now() - timedelta(minutes=2)
        limiter.requests = [old_time, old_time]

        # Should allow new request (old ones expired)
        assert await limiter.allow_request() is True

    def test_rate_limiter_reset(self):
        """Test rate limiter reset."""
        limiter = RateLimiter(5)
        limiter.requests = [datetime.now()] * 5

        limiter.reset()

        assert len(limiter.requests) == 0


class TestModels:
    """Test Pydantic models."""

    def test_tool_config_model(self):
        """Test ToolConfig model."""
        config = ToolConfig(
            tool_type=ToolType.BROWSER,
            name="test_browser",
            description="Test browser tool",
            execution_mode=ToolExecutionMode.SANDBOXED,
            max_execution_time_ms=5000,
            rate_limit_per_minute=20,
        )

        assert config.tool_type == ToolType.BROWSER
        assert config.name == "test_browser"
        assert config.execution_mode == ToolExecutionMode.SANDBOXED

    def test_tool_invocation_model(self):
        """Test ToolInvocation model."""
        invocation = ToolInvocation(
            tool_name="browser",
            parameters={"action": "search", "query": "test"},
            correlation_id="test_123",
        )

        assert invocation.tool_name == "browser"
        assert invocation.parameters["action"] == "search"
        assert invocation.correlation_id == "test_123"

    def test_tool_result_model(self):
        """Test ToolResult model."""
        result = ToolResult(
            tool_name="browser",
            correlation_id="test_123",
            status=ToolStatus.COMPLETED,
            result={"data": "test"},
            execution_time_ms=100.5,
        )

        assert result.tool_name == "browser"
        assert result.status == ToolStatus.COMPLETED
        assert result.result["data"] == "test"

    def test_tool_chain_model(self):
        """Test ToolChain model."""
        chain = ToolChain(
            chain_id="chain_123",
            steps=[
                ToolInvocation(
                    tool_name="browser",
                    parameters={"action": "search"},
                    correlation_id="step_1",
                ),
                ToolInvocation(
                    tool_name="python",
                    parameters={"code": "print()"},
                    correlation_id="step_2",
                ),
            ],
            parallel_groups=[[0], [1]],
            context_passing={"step_1.result": "step_2.input"},
        )

        assert chain.chain_id == "chain_123"
        assert len(chain.steps) == 2
        assert chain.max_chain_time_ms == 120000

    def test_tool_type_enum(self):
        """Test ToolType enum."""
        assert ToolType.BROWSER.value == "browser"
        assert ToolType.PYTHON.value == "python"
        assert ToolType.BASH.value == "bash"
        assert ToolType.DATABASE.value == "database"

    def test_tool_execution_mode_enum(self):
        """Test ToolExecutionMode enum."""
        assert ToolExecutionMode.SANDBOXED.value == "sandboxed"
        assert ToolExecutionMode.RESTRICTED.value == "restricted"
        assert ToolExecutionMode.TRUSTED.value == "trusted"

    def test_tool_status_enum(self):
        """Test ToolStatus enum."""
        assert ToolStatus.PENDING.value == "pending"
        assert ToolStatus.RUNNING.value == "running"
        assert ToolStatus.COMPLETED.value == "completed"
        assert ToolStatus.FAILED.value == "failed"
        assert ToolStatus.TIMEOUT.value == "timeout"
        assert ToolStatus.RATE_LIMITED.value == "rate_limited"

    def test_supported_stages(self):
        """Test that plugin only supports DO stage."""
        assert GPTOSSToolOrchestrator.supported_stages == [WorkflowExecutor.DO]

    def test_required_dependencies(self):
        """Test that plugin declares correct dependencies."""
        deps = GPTOSSToolOrchestrator.dependencies
        assert "llm" in deps
        assert "memory" in deps
        assert "sandbox" in deps
