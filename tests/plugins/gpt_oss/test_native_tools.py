"""Unit tests for Native Tool Orchestrator Plugin."""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from entity.plugins.context import PluginContext
from entity.plugins.gpt_oss.native_tools import (
    BrowserSearchInput,
    BrowserSearchOutput,
    BrowserTool,
    GPTOSSToolOrchestrator,
    PythonCodeInput,
    PythonCodeOutput,
    PythonTool,
    ToolExecutionResult,
    ToolStatus,
    ToolType,
)
from entity.workflow.executor import WorkflowExecutor


class TestBrowserTool:
    """Test BrowserTool functionality."""

    @pytest.fixture
    def browser_tool(self):
        """Create a browser tool for testing."""
        return BrowserTool(rate_limit_requests=5, rate_limit_window=10)

    @pytest.mark.asyncio
    async def test_browser_search_success(self, browser_tool):
        """Test successful browser search."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "AbstractText": "Test abstract text",
                "Heading": "Test Heading",
                "AbstractURL": "https://example.com",
                "RelatedTopics": [
                    {
                        "Text": "Related topic text",
                        "FirstURL": {
                            "Text": "Topic Title",
                            "Result": "https://topic.com",
                        },
                    }
                ],
            }

            mock_client.return_value.__aenter__.return_value.get.return_value = (
                mock_response
            )

            input_data = BrowserSearchInput(query="test query", max_results=3)
            result = await browser_tool.search(input_data)

            assert isinstance(result, BrowserSearchOutput)
            assert result.query == "test query"
            assert len(result.results) >= 1
            assert result.results[0]["title"] == "Test Heading"
            assert result.results[0]["snippet"] == "Test abstract text"
            assert result.execution_time > 0

    @pytest.mark.asyncio
    async def test_browser_search_fallback(self, browser_tool):
        """Test browser search with fallback when API fails."""
        with patch("httpx.AsyncClient") as mock_client:
            # Simulate API failure
            mock_client.return_value.__aenter__.return_value.get.side_effect = (
                Exception("API Error")
            )

            input_data = BrowserSearchInput(query="test query", max_results=3)
            result = await browser_tool.search(input_data)

            assert isinstance(result, BrowserSearchOutput)
            assert result.query == "test query"
            assert len(result.results) == 1
            assert "Search failed" in result.results[0]["snippet"]

    def test_browser_rate_limiting(self, browser_tool):
        """Test browser tool rate limiting."""
        # Initially should be under limit
        assert browser_tool._check_rate_limit() is True

        # Add requests to approach limit
        now = datetime.now()
        browser_tool.request_history = [now - timedelta(seconds=i) for i in range(4)]

        # Should still be under limit (4 requests, limit is 5)
        assert browser_tool._check_rate_limit() is True

        # Add one more to reach exactly the limit
        browser_tool.request_history.append(now)
        # Should be blocked (5 requests, limit is 5, no more allowed)
        assert browser_tool._check_rate_limit() is False

        # Adding more should also be blocked
        browser_tool.request_history.append(now)
        assert browser_tool._check_rate_limit() is False

        # Old requests should be cleaned up
        browser_tool.request_history = [
            now - timedelta(seconds=15)
            for _ in range(10)  # Outside window
        ]
        assert browser_tool._check_rate_limit() is True

    @pytest.mark.asyncio
    async def test_browser_rate_limit_exception(self, browser_tool):
        """Test rate limit exception."""
        # Exceed rate limit
        now = datetime.now()
        browser_tool.request_history = [now for _ in range(6)]

        input_data = BrowserSearchInput(query="test query")
        with pytest.raises(Exception, match="Rate limit exceeded"):
            await browser_tool.search(input_data)

    def test_browser_tool_config(self, browser_tool):
        """Test browser tool configuration."""
        config = browser_tool.tool_config

        assert config["type"] == "function"
        assert config["name"] == "browser_search"
        assert "description" in config
        assert "parameters" in config
        assert config["parameters"]["properties"]["query"]["type"] == "string"


class TestPythonTool:
    """Test PythonTool functionality."""

    @pytest.fixture
    def python_tool(self):
        """Create a python tool for testing."""
        return PythonTool(default_timeout=5.0, default_memory_mb=50)

    @pytest.mark.asyncio
    async def test_python_execute_simple(self, python_tool):
        """Test simple Python code execution."""
        input_data = PythonCodeInput(code="print('Hello, World!')", timeout=10.0)

        with patch.object(python_tool, "_execute_in_sandbox") as mock_execute:
            mock_execute.return_value = {
                "stdout": "Hello, World!\n",
                "stderr": "",
                "exit_code": 0,
                "memory_used_mb": 10.5,
            }

            result = await python_tool.execute(input_data)

            assert isinstance(result, PythonCodeOutput)
            assert result.stdout == "Hello, World!\n"
            assert result.stderr == ""
            assert result.exit_code == 0
            assert result.execution_time > 0

    @pytest.mark.asyncio
    async def test_python_execute_with_error(self, python_tool):
        """Test Python code execution with error."""
        input_data = PythonCodeInput(code="print(undefined_variable)", timeout=10.0)

        with patch.object(python_tool, "_execute_in_sandbox") as mock_execute:
            mock_execute.return_value = {
                "stdout": "",
                "stderr": "NameError: name 'undefined_variable' is not defined",
                "exit_code": 1,
                "memory_used_mb": None,
            }

            result = await python_tool.execute(input_data)

            assert isinstance(result, PythonCodeOutput)
            assert result.stderr != ""
            assert result.exit_code == 1

    def test_python_code_safety_validation(self, python_tool):
        """Test Python code safety validation."""
        # Safe code
        assert python_tool._validate_code_safety("print('hello')") is True
        assert python_tool._validate_code_safety("x = 1 + 2\nprint(x)") is True

        # Unsafe code
        assert python_tool._validate_code_safety("import os") is False
        assert python_tool._validate_code_safety("from subprocess import call") is False
        assert python_tool._validate_code_safety("eval('malicious code')") is False
        assert python_tool._validate_code_safety("exec('dangerous')") is False
        assert python_tool._validate_code_safety("open('/etc/passwd')") is False

    @pytest.mark.asyncio
    async def test_python_unsafe_code_rejection(self, python_tool):
        """Test rejection of unsafe Python code."""
        input_data = PythonCodeInput(code="import os; os.system('rm -rf /')")

        # This should raise an exception before execution
        with pytest.raises(Exception, match="unsafe operations"):
            await python_tool.execute(input_data)

    def test_python_tool_config(self, python_tool):
        """Test Python tool configuration."""
        config = python_tool.tool_config

        assert config["type"] == "function"
        assert config["name"] == "python_execute"
        assert "description" in config
        assert "parameters" in config
        assert config["parameters"]["properties"]["code"]["type"] == "string"

    @pytest.mark.asyncio
    async def test_python_execute_in_sandbox_timeout(self, python_tool):
        """Test sandbox execution timeout."""
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = MagicMock()
            mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
            mock_process.kill = MagicMock()
            mock_process.wait = AsyncMock()
            mock_subprocess.return_value = mock_process

            result = await python_tool._execute_in_sandbox("test.py", 1.0, 100)

            assert result["exit_code"] == 1
            assert "timed out" in result["stderr"]


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

        mock_logging = MagicMock()
        mock_logging.log = AsyncMock()

        return {
            "llm": mock_llm,
            "memory": MockMemory(),
            "logging": mock_logging,
        }

    @pytest.fixture
    def orchestrator(self, mock_resources):
        """Create orchestrator instance for testing."""
        config = {
            "enable_browser_tool": True,
            "enable_python_tool": True,
            "browser_rate_limit_requests": 5,
            "python_default_timeout": 10.0,
        }
        return GPTOSSToolOrchestrator(mock_resources, config)

    @pytest.fixture
    def context(self, mock_resources):
        """Create mock plugin context."""
        ctx = PluginContext(mock_resources, "test_user")
        ctx.current_stage = WorkflowExecutor.DO
        ctx.message = "Test task message"
        ctx.get_resource = lambda name: mock_resources.get(name)
        return ctx

    def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initialization."""
        assert orchestrator.browser_tool is not None
        assert orchestrator.python_tool is not None
        assert orchestrator.config.enable_browser_tool is True
        assert orchestrator.config.enable_python_tool is True

    def test_orchestrator_disabled_tools(self, mock_resources):
        """Test orchestrator with disabled tools."""
        config = {"enable_browser_tool": False, "enable_python_tool": False}
        orchestrator = GPTOSSToolOrchestrator(mock_resources, config)

        assert orchestrator.browser_tool is None
        assert orchestrator.python_tool is None

    def test_get_available_tools(self, orchestrator):
        """Test getting available tools."""
        tools = orchestrator._get_available_tools()

        assert len(tools) == 2
        tool_names = [tool["name"] for tool in tools]
        assert "browser_search" in tool_names
        assert "python_execute" in tool_names

    @pytest.mark.asyncio
    async def test_browser_search_wrapper(self, orchestrator):
        """Test browser search wrapper."""
        with patch.object(orchestrator.browser_tool, "search") as mock_search:
            mock_search.return_value = BrowserSearchOutput(
                query="test",
                results=[{"title": "Test", "snippet": "Result", "url": "http://test"}],
                total_found=1,
                execution_time=0.1,
            )

            result = await orchestrator._browser_search_wrapper(
                query="test", max_results=5
            )

            assert isinstance(result, BrowserSearchOutput)
            assert result.query == "test"
            mock_search.assert_called_once()

    @pytest.mark.asyncio
    async def test_python_execute_wrapper(self, orchestrator):
        """Test Python execute wrapper."""
        with patch.object(orchestrator.python_tool, "execute") as mock_execute:
            mock_execute.return_value = PythonCodeOutput(
                code="print('test')",
                stdout="test\n",
                stderr="",
                exit_code=0,
                execution_time=0.1,
            )

            result = await orchestrator._python_execute_wrapper(code="print('test')")

            assert isinstance(result, PythonCodeOutput)
            assert result.stdout == "test\n"
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_python_wrapper_code_length_limit(self, orchestrator):
        """Test Python wrapper code length validation."""
        orchestrator.config.python_max_code_length = 10

        with pytest.raises(Exception, match="Code too long"):
            await orchestrator._python_execute_wrapper(code="x" * 20)

    @pytest.mark.asyncio
    async def test_execute_impl_basic(self, orchestrator, context):
        """Test basic execute implementation."""
        context.remember = AsyncMock()
        context.log = AsyncMock()

        result = await orchestrator._execute_impl(context)

        assert result == context.message
        context.remember.assert_called_once()
        context.log.assert_called_once()

        # Check that tools were stored
        call_args = context.remember.call_args
        assert call_args[0][0] == "available_native_tools"
        assert len(call_args[0][1]) == 2  # Both tools available

    @pytest.mark.asyncio
    async def test_execute_tool_chain_success(self, orchestrator, context):
        """Test successful tool chain execution."""
        tool_calls = [
            {"name": "browser_search", "arguments": {"query": "test"}},
            {"name": "python_execute", "arguments": {"code": "print('hello')"}},
        ]

        with patch.object(orchestrator, "_execute_single_tool") as mock_execute_single:
            mock_execute_single.side_effect = [
                ToolExecutionResult(
                    tool_type=ToolType.BROWSER,
                    status=ToolStatus.COMPLETED,
                    result="search results",
                ),
                ToolExecutionResult(
                    tool_type=ToolType.PYTHON,
                    status=ToolStatus.COMPLETED,
                    result="hello\n",
                ),
            ]

            results = await orchestrator.execute_tool_chain(context, tool_calls)

            assert len(results) == 2
            assert all(result.status == ToolStatus.COMPLETED for result in results)

    @pytest.mark.asyncio
    async def test_execute_tool_chain_too_many_tools(self, orchestrator, context):
        """Test tool chain with too many tools."""
        orchestrator.config.max_chained_tools = 2
        tool_calls = [{"name": "browser_search"}] * 5

        with pytest.raises(Exception, match="Too many chained tools"):
            await orchestrator.execute_tool_chain(context, tool_calls)

    @pytest.mark.asyncio
    async def test_execute_single_tool_browser(self, orchestrator, context):
        """Test executing single browser tool."""
        tool_call = {"name": "browser_search", "arguments": {"query": "test"}}

        with patch.object(orchestrator, "_browser_search_wrapper") as mock_search:
            mock_search.return_value = BrowserSearchOutput(
                query="test",
                results=[],
                total_found=0,
                execution_time=0.1,
            )

            result = await orchestrator._execute_single_tool(context, tool_call)

            assert result.tool_type == ToolType.BROWSER
            assert result.status == ToolStatus.COMPLETED
            mock_search.assert_called_once_with(query="test")

    @pytest.mark.asyncio
    async def test_execute_single_tool_python(self, orchestrator, context):
        """Test executing single Python tool."""
        tool_call = {"name": "python_execute", "arguments": {"code": "print('test')"}}

        with patch.object(orchestrator, "_python_execute_wrapper") as mock_execute:
            mock_execute.return_value = PythonCodeOutput(
                code="print('test')",
                stdout="test\n",
                stderr="",
                exit_code=0,
                execution_time=0.1,
            )

            result = await orchestrator._execute_single_tool(context, tool_call)

            assert result.tool_type == ToolType.PYTHON
            assert result.status == ToolStatus.COMPLETED
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_single_tool_unknown(self, orchestrator, context):
        """Test executing unknown tool."""
        tool_call = {"name": "unknown_tool", "arguments": {}}

        result = await orchestrator._execute_single_tool(context, tool_call)

        assert result.status == ToolStatus.FAILED
        assert "Unknown or disabled tool" in result.error

    @pytest.mark.asyncio
    async def test_execute_single_tool_exception(self, orchestrator, context):
        """Test executing tool with exception."""
        tool_call = {"name": "browser_search", "arguments": {"query": "test"}}

        with patch.object(orchestrator, "_browser_search_wrapper") as mock_search:
            mock_search.side_effect = Exception("Tool error")

            result = await orchestrator._execute_single_tool(context, tool_call)

            assert result.status == ToolStatus.FAILED
            assert "Tool error" in result.error

    def test_orchestrator_config_validation(self, mock_resources):
        """Test configuration validation."""
        # Valid config
        config = {
            "enable_browser_tool": True,
            "browser_rate_limit_requests": 10,
            "python_default_timeout": 30.0,
        }
        orchestrator = GPTOSSToolOrchestrator(mock_resources, config)
        assert orchestrator.config.enable_browser_tool is True

        # Empty config should work (uses defaults)
        orchestrator_default = GPTOSSToolOrchestrator(mock_resources, {})
        assert orchestrator_default.config.enable_browser_tool is True  # Default value

    @pytest.mark.asyncio
    async def test_tool_registration(self, orchestrator):
        """Test that tools are properly registered."""
        # This would require access to the global registry
        # For now, just test that the registration method runs without error
        orchestrator._register_tools()  # Should not raise

    def test_model_classes(self):
        """Test Pydantic model classes."""
        # Test BrowserSearchInput
        browser_input = BrowserSearchInput(query="test query", max_results=10)
        assert browser_input.query == "test query"
        assert browser_input.max_results == 10

        # Test PythonCodeInput
        python_input = PythonCodeInput(code="print('hello')", timeout=60.0)
        assert python_input.code == "print('hello')"
        assert python_input.timeout == 60.0

        # Test ToolExecutionResult
        result = ToolExecutionResult(
            tool_type=ToolType.BROWSER, status=ToolStatus.COMPLETED, result="success"
        )
        assert result.tool_type == ToolType.BROWSER
        assert result.status == ToolStatus.COMPLETED
        assert result.result == "success"

    def test_enum_classes(self):
        """Test enum classes."""
        assert ToolType.BROWSER.value == "browser"
        assert ToolType.PYTHON.value == "python"

        assert ToolStatus.PENDING.value == "pending"
        assert ToolStatus.COMPLETED.value == "completed"
        assert ToolStatus.FAILED.value == "failed"
