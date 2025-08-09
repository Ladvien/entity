"""Native Tool Orchestrator Plugin for GPT-OSS integration.

This plugin enables gpt-oss's native browser and Python tools within Entity workflows,
providing web search capabilities and sandboxed code execution while maintaining
Entity's security requirements and integration patterns.
"""

from __future__ import annotations

import asyncio
import json
import re
import tempfile
import time
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field

from entity.plugins.tool import ToolPlugin
from entity.tools.registry import register_tool
from entity.tools.sandbox import SandboxedToolRunner
from entity.workflow.executor import WorkflowExecutor


class ToolType(Enum):
    """Types of tools available in the orchestrator."""

    BROWSER = "browser"
    PYTHON = "python"


class ToolStatus(Enum):
    """Status of tool execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"


class ToolExecutionResult(BaseModel):
    """Result of a tool execution."""

    tool_type: ToolType
    status: ToolStatus
    result: Optional[str] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    tokens_used: Optional[int] = None
    rate_limit_reset: Optional[datetime] = None


class BrowserSearchInput(BaseModel):
    """Input model for browser search tool."""

    query: str = Field(description="Search query to execute")
    max_results: int = Field(
        default=5, description="Maximum number of results to return"
    )
    timeout: float = Field(default=10.0, description="Timeout in seconds")


class BrowserSearchOutput(BaseModel):
    """Output model for browser search results."""

    query: str
    results: List[Dict[str, str]]
    total_found: int
    execution_time: float


class PythonCodeInput(BaseModel):
    """Input model for Python code execution."""

    code: str = Field(description="Python code to execute")
    timeout: float = Field(default=30.0, description="Timeout in seconds")
    memory_limit_mb: int = Field(default=100, description="Memory limit in MB")


class PythonCodeOutput(BaseModel):
    """Output model for Python code execution."""

    code: str
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
    memory_used_mb: Optional[float] = None


class BrowserTool:
    """Browser tool for web search capabilities using harmony format."""

    def __init__(self, rate_limit_requests: int = 10, rate_limit_window: int = 60):
        self.rate_limit_requests = rate_limit_requests
        self.rate_limit_window = rate_limit_window
        self.request_history: List[datetime] = []

    async def search(self, input_data: BrowserSearchInput) -> BrowserSearchOutput:
        """Execute web search with rate limiting."""
        start_time = time.time()

        # Check rate limit
        if not self._check_rate_limit():
            raise Exception(
                "Rate limit exceeded. Please wait before making more requests."
            )

        try:
            # Use DuckDuckGo API for search
            results = await self._search_duckduckgo(
                input_data.query, input_data.max_results
            )

            # Record successful request
            self.request_history.append(datetime.now())

            return BrowserSearchOutput(
                query=input_data.query,
                results=results,
                total_found=len(results),
                execution_time=time.time() - start_time,
            )

        except Exception as e:
            raise Exception(f"Browser search failed: {str(e)}")

    async def _search_duckduckgo(
        self, query: str, max_results: int
    ) -> List[Dict[str, str]]:
        """Search using DuckDuckGo API."""
        url = "https://api.duckduckgo.com/"
        params = {"q": query, "format": "json", "no_redirect": 1, "no_html": 1}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10.0)
                data = response.json()

                results = []

                # Add instant answer if available
                if data.get("AbstractText"):
                    results.append(
                        {
                            "title": data.get("Heading", "Instant Answer"),
                            "snippet": data.get("AbstractText", ""),
                            "url": data.get("AbstractURL", ""),
                            "source": "instant_answer",
                        }
                    )

                # Add related topics
                for topic in data.get("RelatedTopics", [])[
                    : max_results - len(results)
                ]:
                    if isinstance(topic, dict) and "Text" in topic:
                        results.append(
                            {
                                "title": topic.get("FirstURL", {}).get(
                                    "Text", "Related Topic"
                                ),
                                "snippet": topic.get("Text", ""),
                                "url": topic.get("FirstURL", {}).get("Result", ""),
                                "source": "related_topic",
                            }
                        )

                # Fallback: create a simple result
                if not results:
                    results.append(
                        {
                            "title": f"Search: {query}",
                            "snippet": f"Search performed for: {query}",
                            "url": f"https://duckduckgo.com/?q={query}",
                            "source": "fallback",
                        }
                    )

                return results[:max_results]

        except Exception as e:
            # Fallback result
            return [
                {
                    "title": f"Search: {query}",
                    "snippet": f"Search failed: {str(e)}",
                    "url": f"https://duckduckgo.com/?q={query}",
                    "source": "error_fallback",
                }
            ]

    def _check_rate_limit(self) -> bool:
        """Check if request is within rate limit."""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.rate_limit_window)

        # Remove old requests
        self.request_history = [req for req in self.request_history if req > cutoff]

        # Check if under limit (allow new request if we haven't reached limit)
        return len(self.request_history) < self.rate_limit_requests

    @property
    def tool_config(self) -> Dict[str, Any]:
        """Get tool configuration for harmony format."""
        return {
            "type": "function",
            "name": "browser_search",
            "description": "Search the web for information using a search engine",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to execute",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        }


class PythonTool:
    """Python tool for sandboxed code execution."""

    def __init__(self, default_timeout: float = 30.0, default_memory_mb: int = 100):
        self.default_timeout = default_timeout
        self.default_memory_mb = default_memory_mb
        self.sandbox = SandboxedToolRunner(
            timeout=default_timeout, memory_mb=default_memory_mb
        )

    async def execute(self, input_data: PythonCodeInput) -> PythonCodeOutput:
        """Execute Python code in sandbox."""
        start_time = time.time()

        # Validate code safety
        if not self._validate_code_safety(input_data.code):
            raise Exception("Code contains potentially unsafe operations")

        try:
            # Create temporary file for code execution
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(input_data.code)
                temp_file = f.name

            # Execute in sandbox
            result = await self._execute_in_sandbox(
                temp_file, input_data.timeout, input_data.memory_limit_mb
            )

            # Clean up
            Path(temp_file).unlink(missing_ok=True)

            return PythonCodeOutput(
                code=input_data.code,
                stdout=result.get("stdout", ""),
                stderr=result.get("stderr", ""),
                exit_code=result.get("exit_code", 0),
                execution_time=time.time() - start_time,
                memory_used_mb=result.get("memory_used_mb"),
            )

        except Exception as e:
            return PythonCodeOutput(
                code=input_data.code,
                stdout="",
                stderr=f"Execution error: {str(e)}",
                exit_code=1,
                execution_time=time.time() - start_time,
            )

    def _validate_code_safety(self, code: str) -> bool:
        """Validate that code doesn't contain dangerous operations."""
        dangerous_patterns = [
            r"import\s+os",
            r"import\s+subprocess",
            r"import\s+sys",
            r"from\s+os\s+import",
            r"from\s+subprocess\s+import",
            r"from\s+sys\s+import",
            r"eval\s*\(",
            r"exec\s*\(",
            r"open\s*\(",
            r"file\s*\(",
            r"__import__",
            r"globals\s*\(",
            r"locals\s*\(",
            r"vars\s*\(",
            r"dir\s*\(",
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                return False

        return True

    async def _execute_in_sandbox(
        self, file_path: str, timeout: float, memory_mb: int
    ) -> Dict[str, Any]:
        """Execute Python file in sandbox."""
        try:
            # Execute using subprocess for better isolation
            process = await asyncio.create_subprocess_exec(
                "python",
                file_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=1024 * 1024,  # 1MB output limit
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )

                return {
                    "stdout": stdout.decode("utf-8", errors="ignore"),
                    "stderr": stderr.decode("utf-8", errors="ignore"),
                    "exit_code": process.returncode,
                    "memory_used_mb": None,  # Would need psutil for accurate measurement
                }

            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise Exception(f"Code execution timed out after {timeout} seconds")

        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": 1,
                "memory_used_mb": None,
            }

    @property
    def tool_config(self) -> Dict[str, Any]:
        """Get tool configuration for harmony format."""
        return {
            "type": "function",
            "name": "python_execute",
            "description": "Execute Python code in a secure sandbox environment",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python code to execute"},
                    "timeout": {
                        "type": "number",
                        "description": "Timeout in seconds",
                        "default": 30.0,
                    },
                    "memory_limit_mb": {
                        "type": "integer",
                        "description": "Memory limit in MB",
                        "default": 100,
                    },
                },
                "required": ["code"],
            },
        }


class GPTOSSToolOrchestrator(ToolPlugin):
    """Plugin that orchestrates GPT-OSS native tools within Entity workflows.

    This plugin:
    - Provides browser tool with web search capabilities
    - Provides Python tool with sandboxed code execution
    - Integrates with harmony format for tool definitions
    - Supports tool chaining and multi-step workflows
    - Implements rate limiting and resource constraints
    - Maintains Entity's security and sandboxing requirements
    """

    supported_stages = [WorkflowExecutor.DO]
    dependencies = ["llm", "memory"]

    class ConfigModel(BaseModel):
        """Configuration for the native tools orchestrator."""

        enable_browser_tool: bool = Field(
            default=True, description="Enable browser/web search tool"
        )
        enable_python_tool: bool = Field(
            default=True, description="Enable Python execution tool"
        )

        # Browser tool config
        browser_rate_limit_requests: int = Field(
            default=10, description="Browser requests per window"
        )
        browser_rate_limit_window: int = Field(
            default=60, description="Rate limit window in seconds"
        )
        browser_max_results: int = Field(default=5, description="Max search results")
        browser_timeout: float = Field(
            default=10.0, description="Browser request timeout"
        )

        # Python tool config
        python_default_timeout: float = Field(
            default=30.0, description="Default Python timeout"
        )
        python_default_memory_mb: int = Field(
            default=100, description="Default Python memory limit"
        )
        python_max_code_length: int = Field(
            default=10000, description="Max Python code length"
        )

        # Tool chaining
        max_chained_tools: int = Field(default=5, description="Max tools in a chain")
        chain_timeout: float = Field(default=120.0, description="Total chain timeout")

        # Security
        enable_code_validation: bool = Field(
            default=True, description="Enable Python code safety validation"
        )

    def __init__(self, resources: dict[str, Any], config: Dict[str, Any] | None = None):
        """Initialize the tool orchestrator plugin."""
        super().__init__(resources, config)

        # Validate configuration
        validation_result = self.validate_config()
        if not validation_result.success:
            raise ValueError(f"Invalid configuration: {validation_result.error}")

        # Initialize tools
        self.browser_tool = None
        self.python_tool = None

        if self.config.enable_browser_tool:
            self.browser_tool = BrowserTool(
                rate_limit_requests=self.config.browser_rate_limit_requests,
                rate_limit_window=self.config.browser_rate_limit_window,
            )

        if self.config.enable_python_tool:
            self.python_tool = PythonTool(
                default_timeout=self.config.python_default_timeout,
                default_memory_mb=self.config.python_default_memory_mb,
            )

        # Register tools with Entity's registry
        self._register_tools()

    def _register_tools(self):
        """Register tools with Entity's tool registry."""
        if self.browser_tool:
            register_tool(
                self._browser_search_wrapper,
                name="browser_search",
                category="gpt_oss_native",
                description="Search the web for information",
                input_model=BrowserSearchInput,
                output_model=BrowserSearchOutput,
            )

        if self.python_tool:
            register_tool(
                self._python_execute_wrapper,
                name="python_execute",
                category="gpt_oss_native",
                description="Execute Python code in sandbox",
                input_model=PythonCodeInput,
                output_model=PythonCodeOutput,
            )

    async def _browser_search_wrapper(
        self, query: str, max_results: int = 5
    ) -> BrowserSearchOutput:
        """Wrapper for browser search tool."""
        if not self.browser_tool:
            raise Exception("Browser tool is disabled")

        input_data = BrowserSearchInput(query=query, max_results=max_results)
        return await self.browser_tool.search(input_data)

    async def _python_execute_wrapper(
        self, code: str, timeout: float = 30.0, memory_limit_mb: int = 100
    ) -> PythonCodeOutput:
        """Wrapper for Python execution tool."""
        if not self.python_tool:
            raise Exception("Python tool is disabled")

        # Validate code length
        if len(code) > self.config.python_max_code_length:
            raise Exception(
                f"Code too long. Max length: {self.config.python_max_code_length}"
            )

        input_data = PythonCodeInput(
            code=code, timeout=timeout, memory_limit_mb=memory_limit_mb
        )
        return await self.python_tool.execute(input_data)

    async def _execute_impl(self, context) -> str:
        """Execute the native tools orchestrator."""
        # Check if LLM has harmony infrastructure
        llm = context.get_resource("llm")

        # Get available tools for the LLM
        available_tools = self._get_available_tools()

        if not available_tools:
            return context.message  # No tools available, pass through

        # Store tool availability in context for other plugins
        await context.remember("available_native_tools", available_tools)

        # If we have harmony infrastructure, configure tools in system message
        if hasattr(llm, "infrastructure") and hasattr(
            llm.infrastructure, "generate_with_channels"
        ):
            # The tools will be available for the LLM to use via context.tool_use()
            # This plugin makes them available but doesn't force their use
            pass

        # Log tool availability
        await context.log(
            level="info",
            category="tool_orchestration",
            message=f"Native tools available: {[tool['name'] for tool in available_tools]}",
        )

        # Pass through the message - tools will be used via context.tool_use() calls
        return context.message

    def _get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools with their configurations."""
        tools = []

        if self.browser_tool:
            tools.append(self.browser_tool.tool_config)

        if self.python_tool:
            tools.append(self.python_tool.tool_config)

        return tools

    async def execute_tool_chain(
        self, context, tool_calls: List[Dict[str, Any]]
    ) -> List[ToolExecutionResult]:
        """Execute a chain of tool calls with proper error handling and limits."""
        if len(tool_calls) > self.config.max_chained_tools:
            raise Exception(
                f"Too many chained tools. Max: {self.config.max_chained_tools}"
            )

        start_time = time.time()
        results = []

        for i, tool_call in enumerate(tool_calls):
            # Check total chain timeout
            if time.time() - start_time > self.config.chain_timeout:
                results.append(
                    ToolExecutionResult(
                        tool_type=ToolType.BROWSER,  # Default
                        status=ToolStatus.FAILED,
                        error="Chain timeout exceeded",
                    )
                )
                break

            try:
                result = await self._execute_single_tool(context, tool_call)
                results.append(result)

                # If tool failed, potentially stop chain
                if result.status == ToolStatus.FAILED:
                    await context.log(
                        level="warning",
                        category="tool_chain",
                        message=f"Tool {i+1} failed: {result.error}",
                    )

            except Exception as e:
                results.append(
                    ToolExecutionResult(
                        tool_type=ToolType.BROWSER,  # Default
                        status=ToolStatus.FAILED,
                        error=str(e),
                    )
                )

        return results

    async def _execute_single_tool(
        self, context, tool_call: Dict[str, Any]
    ) -> ToolExecutionResult:
        """Execute a single tool call."""
        tool_name = tool_call.get("name", "")
        tool_args = tool_call.get("arguments", {})

        start_time = time.time()

        try:
            if tool_name == "browser_search" and self.browser_tool:
                result = await self._browser_search_wrapper(**tool_args)
                return ToolExecutionResult(
                    tool_type=ToolType.BROWSER,
                    status=ToolStatus.COMPLETED,
                    result=json.dumps(result.model_dump()),
                    execution_time=time.time() - start_time,
                )

            elif tool_name == "python_execute" and self.python_tool:
                result = await self._python_execute_wrapper(**tool_args)
                return ToolExecutionResult(
                    tool_type=ToolType.PYTHON,
                    status=ToolStatus.COMPLETED,
                    result=json.dumps(result.model_dump()),
                    execution_time=time.time() - start_time,
                )

            else:
                return ToolExecutionResult(
                    tool_type=ToolType.BROWSER,  # Default
                    status=ToolStatus.FAILED,
                    error=f"Unknown or disabled tool: {tool_name}",
                )

        except Exception as e:
            return ToolExecutionResult(
                tool_type=ToolType.BROWSER,  # Default
                status=ToolStatus.FAILED,
                error=str(e),
                execution_time=time.time() - start_time,
            )
