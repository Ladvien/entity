"""Native Tool Orchestrator Plugin for GPT-OSS integration.

This plugin enables gpt-oss's native browser and Python tools within Entity workflows,
allowing agents to perform web searches and execute code autonomously while maintaining
Entity's sandboxing and security requirements.
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from entity.plugins.base import Plugin
from entity.workflow.executor import WorkflowExecutor


class ToolType(Enum):
    """Types of native tools available in GPT-OSS."""

    BROWSER = "browser"
    PYTHON = "python"
    BASH = "bash"  # Future extension
    DATABASE = "database"  # Future extension


class ToolExecutionMode(Enum):
    """Execution modes for tools."""

    SANDBOXED = "sandboxed"  # Full isolation
    RESTRICTED = "restricted"  # Limited permissions
    TRUSTED = "trusted"  # Full permissions (admin only)


class ToolStatus(Enum):
    """Status of tool execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"


class ToolConfig(BaseModel):
    """Configuration for a single tool."""

    tool_type: ToolType = Field(description="Type of tool")
    name: str = Field(description="Tool name for harmony format")
    description: str = Field(description="Tool description")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Tool parameters schema"
    )
    execution_mode: ToolExecutionMode = Field(
        default=ToolExecutionMode.SANDBOXED,
        description="Execution mode for security",
    )
    max_execution_time_ms: int = Field(
        default=30000, description="Maximum execution time", ge=1000, le=300000
    )
    rate_limit_per_minute: int = Field(
        default=10, description="Rate limit per minute", ge=1, le=100
    )
    resource_limits: Dict[str, Any] = Field(
        default_factory=dict, description="Resource constraints"
    )


class ToolInvocation(BaseModel):
    """A single tool invocation request."""

    tool_name: str = Field(description="Name of tool to invoke")
    parameters: Dict[str, Any] = Field(description="Parameters for tool")
    correlation_id: str = Field(description="Unique ID for this invocation")
    timestamp: datetime = Field(default_factory=datetime.now)
    timeout_ms: Optional[int] = Field(
        default=None, description="Override timeout for this invocation"
    )


class ToolResult(BaseModel):
    """Result from tool execution."""

    tool_name: str = Field(description="Name of tool that was invoked")
    correlation_id: str = Field(description="Correlation ID from invocation")
    status: ToolStatus = Field(description="Execution status")
    result: Optional[Any] = Field(default=None, description="Tool output")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    execution_time_ms: float = Field(default=0, description="Time taken to execute")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ToolChain(BaseModel):
    """A chain of tool invocations for multi-step workflows."""

    chain_id: str = Field(description="Unique chain identifier")
    steps: List[ToolInvocation] = Field(description="Ordered list of tool invocations")
    parallel_groups: List[List[int]] = Field(
        default_factory=list,
        description="Groups of step indices that can run in parallel",
    )
    context_passing: Dict[str, str] = Field(
        default_factory=dict,
        description="Map of output->input for context passing between tools",
    )
    max_chain_time_ms: int = Field(
        default=120000, description="Maximum time for entire chain"
    )


class BrowserTool:
    """Browser tool for web search and navigation."""

    def __init__(self, config: Optional[ToolConfig] = None):
        """Initialize browser tool."""
        self.config = config or ToolConfig(
            tool_type=ToolType.BROWSER,
            name="browser",
            description="Search the web and retrieve information from websites",
            parameters={
                "action": {
                    "type": "string",
                    "enum": ["search", "navigate", "extract"],
                    "description": "Action to perform",
                },
                "query": {
                    "type": "string",
                    "description": "Search query or URL",
                },
                "extract_selector": {
                    "type": "string",
                    "description": "CSS selector for extraction (optional)",
                },
            },
            resource_limits={
                "max_pages": 5,
                "max_content_size_kb": 500,
                "allowed_domains": [],  # Empty = all domains
                "blocked_domains": ["localhost", "127.0.0.1", "internal"],
            },
        )
        self.rate_limiter = RateLimiter(self.config.rate_limit_per_minute)

    async def execute(
        self, parameters: Dict[str, Any], sandbox: Optional[Any] = None
    ) -> ToolResult:
        """Execute browser tool action."""
        correlation_id = f"browser_{int(time.time() * 1000)}"
        start_time = time.time()

        try:
            # Check rate limit
            if not await self.rate_limiter.allow_request():
                return ToolResult(
                    tool_name="browser",
                    correlation_id=correlation_id,
                    status=ToolStatus.RATE_LIMITED,
                    error="Rate limit exceeded",
                )

            action = parameters.get("action", "search")
            query = parameters.get("query", "")

            if not query:
                raise ValueError("Query parameter is required")

            # Validate URL for navigate/extract actions
            if action in ["navigate", "extract"]:
                self._validate_url(query)

            # Execute action based on type
            if action == "search":
                result = await self._search_web(query, sandbox)
            elif action == "navigate":
                result = await self._navigate_to_url(query, sandbox)
            elif action == "extract":
                selector = parameters.get("extract_selector")
                result = await self._extract_content(query, selector, sandbox)
            else:
                raise ValueError(f"Unknown action: {action}")

            execution_time_ms = (time.time() - start_time) * 1000

            return ToolResult(
                tool_name="browser",
                correlation_id=correlation_id,
                status=ToolStatus.COMPLETED,
                result=result,
                execution_time_ms=execution_time_ms,
                metadata={"action": action, "query": query},
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            return ToolResult(
                tool_name="browser",
                correlation_id=correlation_id,
                status=ToolStatus.FAILED,
                error=str(e),
                execution_time_ms=execution_time_ms,
            )

    async def _search_web(self, query: str, sandbox: Optional[Any]) -> Dict[str, Any]:
        """Perform web search."""
        # In production, this would integrate with a real search API
        # For now, return mock results
        await asyncio.sleep(0.5)  # Simulate API call
        return {
            "query": query,
            "results": [
                {
                    "title": f"Result 1 for {query}",
                    "url": "https://example.com/1",
                    "snippet": f"This is a snippet about {query}...",
                },
                {
                    "title": f"Result 2 for {query}",
                    "url": "https://example.com/2",
                    "snippet": f"Another result about {query}...",
                },
            ],
        }

    async def _navigate_to_url(
        self, url: str, sandbox: Optional[Any]
    ) -> Dict[str, Any]:
        """Navigate to URL and get content."""
        # In production, this would use a real browser automation tool
        await asyncio.sleep(0.3)  # Simulate page load
        return {
            "url": url,
            "title": "Page Title",
            "content": f"Content from {url}",
            "metadata": {"status_code": 200, "content_type": "text/html"},
        }

    async def _extract_content(
        self, url: str, selector: Optional[str], sandbox: Optional[Any]
    ) -> Dict[str, Any]:
        """Extract specific content from URL."""
        # Navigate first
        page_data = await self._navigate_to_url(url, sandbox)

        # Extract based on selector
        if selector:
            # In production, would use real DOM parsing
            extracted = f"Extracted content using selector '{selector}'"
        else:
            extracted = page_data["content"]

        return {
            "url": url,
            "selector": selector,
            "extracted": extracted,
        }

    def _validate_url(self, url: str) -> None:
        """Validate URL against security constraints."""
        parsed = urlparse(url)

        # Check blocked domains
        blocked = self.config.resource_limits.get("blocked_domains", [])
        if parsed.hostname in blocked:
            raise ValueError(f"Domain {parsed.hostname} is blocked")

        # Check allowed domains if specified
        allowed = self.config.resource_limits.get("allowed_domains", [])
        if allowed and parsed.hostname not in allowed:
            raise ValueError(f"Domain {parsed.hostname} is not in allowed list")

    def get_harmony_format(self) -> Dict[str, Any]:
        """Get tool configuration in harmony format."""
        return {
            "type": "tool",
            "name": self.config.name,
            "description": self.config.description,
            "parameters": self.config.parameters,
        }


class PythonTool:
    """Python tool for sandboxed code execution."""

    def __init__(self, config: Optional[ToolConfig] = None):
        """Initialize Python tool."""
        self.config = config or ToolConfig(
            tool_type=ToolType.PYTHON,
            name="python",
            description="Execute Python code in a sandboxed environment",
            parameters={
                "code": {
                    "type": "string",
                    "description": "Python code to execute",
                },
                "imports": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of allowed imports",
                },
                "persist_context": {
                    "type": "boolean",
                    "description": "Persist execution context for chaining",
                },
            },
            resource_limits={
                "max_memory_mb": 256,
                "max_cpu_seconds": 10,
                "allowed_modules": [
                    "math",
                    "statistics",
                    "json",
                    "re",
                    "datetime",
                    "collections",
                    "itertools",
                ],
                "blocked_modules": [
                    "os",
                    "sys",
                    "subprocess",
                    "socket",
                    "__builtins__",
                ],
            },
        )
        self.rate_limiter = RateLimiter(self.config.rate_limit_per_minute)
        self.execution_contexts = {}  # Store contexts for chaining

    async def execute(
        self, parameters: Dict[str, Any], sandbox: Optional[Any] = None
    ) -> ToolResult:
        """Execute Python code in sandbox."""
        correlation_id = f"python_{int(time.time() * 1000)}"
        start_time = time.time()

        try:
            # Check rate limit
            if not await self.rate_limiter.allow_request():
                return ToolResult(
                    tool_name="python",
                    correlation_id=correlation_id,
                    status=ToolStatus.RATE_LIMITED,
                    error="Rate limit exceeded",
                )

            code = parameters.get("code", "")
            imports = parameters.get("imports", [])
            persist_context = parameters.get("persist_context", False)

            if not code:
                raise ValueError("Code parameter is required")

            # Validate imports
            self._validate_imports(imports)

            # Validate code safety
            self._validate_code_safety(code)

            # Execute in sandbox
            if sandbox:
                result = await self._execute_in_sandbox(
                    code, imports, persist_context, sandbox
                )
            else:
                result = await self._execute_restricted(code, imports, persist_context)

            execution_time_ms = (time.time() - start_time) * 1000

            return ToolResult(
                tool_name="python",
                correlation_id=correlation_id,
                status=ToolStatus.COMPLETED,
                result=result,
                execution_time_ms=execution_time_ms,
                metadata={
                    "lines_of_code": len(code.split("\n")),
                    "persist_context": persist_context,
                },
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            return ToolResult(
                tool_name="python",
                correlation_id=correlation_id,
                status=ToolStatus.FAILED,
                error=str(e),
                execution_time_ms=execution_time_ms,
            )

    async def _execute_in_sandbox(
        self,
        code: str,
        imports: List[str],
        persist_context: bool,
        sandbox: Any,
    ) -> Dict[str, Any]:
        """Execute code in Entity's sandbox."""
        # Build safe execution environment
        exec_env = self._build_safe_environment(imports)

        # Get or create context
        context_id = sandbox.context_id if hasattr(sandbox, "context_id") else "default"
        if persist_context and context_id in self.execution_contexts:
            exec_env.update(self.execution_contexts[context_id])

        # Execute in sandbox
        result = await sandbox.run(
            self._execute_code,
            code,
            exec_env,
            timeout=self.config.max_execution_time_ms / 1000,
        )

        # Persist context if requested
        if persist_context:
            self.execution_contexts[context_id] = exec_env

        return result

    async def _execute_restricted(
        self, code: str, imports: List[str], persist_context: bool
    ) -> Dict[str, Any]:
        """Execute code with restrictions (no sandbox available)."""
        # Build safe execution environment
        exec_env = self._build_safe_environment(imports)

        # Simple restricted execution (not production-ready)
        # In production, use proper sandboxing like RestrictedPython
        try:
            # Create a restricted globals dict
            restricted_globals = {
                "__builtins__": {
                    "print": print,
                    "len": len,
                    "range": range,
                    "str": str,
                    "int": int,
                    "float": float,
                    "list": list,
                    "dict": dict,
                    "tuple": tuple,
                    "set": set,
                    "bool": bool,
                    "type": type,
                    "isinstance": isinstance,
                    "sum": sum,
                    "min": min,
                    "max": max,
                    "abs": abs,
                    "round": round,
                    "sorted": sorted,
                    "enumerate": enumerate,
                    "zip": zip,
                    "map": map,
                    "filter": filter,
                    "any": any,
                    "all": all,
                }
            }
            restricted_globals.update(exec_env)

            # Capture output
            output = []
            original_print = print

            def capture_print(*args, **kwargs):
                output.append(" ".join(str(arg) for arg in args))

            restricted_globals["__builtins__"]["print"] = capture_print

            # Execute code
            exec(code, restricted_globals, {})

            # Restore print
            restricted_globals["__builtins__"]["print"] = original_print

            return {
                "output": "\n".join(output) if output else None,
                "success": True,
            }

        except Exception as e:
            return {
                "output": None,
                "success": False,
                "error": str(e),
            }

    def _build_safe_environment(self, imports: List[str]) -> Dict[str, Any]:
        """Build safe execution environment with allowed imports."""
        env = {}

        for module_name in imports:
            if module_name in self.config.resource_limits["allowed_modules"]:
                # Safe to import these modules
                if module_name == "math":
                    import math

                    env["math"] = math
                elif module_name == "json":
                    import json

                    env["json"] = json
                elif module_name == "re":
                    import re

                    env["re"] = re
                elif module_name == "datetime":
                    import datetime

                    env["datetime"] = datetime
                elif module_name == "collections":
                    import collections

                    env["collections"] = collections
                elif module_name == "itertools":
                    import itertools

                    env["itertools"] = itertools
                elif module_name == "statistics":
                    import statistics

                    env["statistics"] = statistics

        return env

    def _validate_imports(self, imports: List[str]) -> None:
        """Validate requested imports against security policy."""
        blocked = self.config.resource_limits.get("blocked_modules", [])
        for module in imports:
            if module in blocked:
                raise ValueError(f"Module '{module}' is blocked for security reasons")

        allowed = self.config.resource_limits.get("allowed_modules", [])
        for module in imports:
            if module not in allowed:
                raise ValueError(f"Module '{module}' is not in allowed list")

    def _validate_code_safety(self, code: str) -> None:
        """Basic code safety validation."""
        # Check for dangerous patterns
        dangerous_patterns = [
            r"__import__",
            r"exec\s*\(",
            r"eval\s*\(",
            r"compile\s*\(",
            r"open\s*\(",
            r"file\s*\(",
            r"input\s*\(",
            r"raw_input\s*\(",
            r"__.*__",  # Dunder methods
            r"getattr\s*\(",
            r"setattr\s*\(",
            r"delattr\s*\(",
            r"globals\s*\(",
            r"locals\s*\(",
            r"vars\s*\(",
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, code):
                raise ValueError(f"Dangerous pattern detected: {pattern}")

    async def _execute_code(
        self, code: str, exec_env: Dict[str, Any], timeout: float
    ) -> Dict[str, Any]:
        """Execute code with timeout."""
        # This would be called within the sandbox
        # Implementation depends on the sandbox system
        return {"output": f"Executed: {code[:50]}...", "success": True}

    def get_harmony_format(self) -> Dict[str, Any]:
        """Get tool configuration in harmony format."""
        return {
            "type": "tool",
            "name": self.config.name,
            "description": self.config.description,
            "parameters": self.config.parameters,
        }


class RateLimiter:
    """Simple rate limiter for tool execution."""

    def __init__(self, max_requests_per_minute: int):
        """Initialize rate limiter."""
        self.max_requests = max_requests_per_minute
        self.requests = []
        self.lock = asyncio.Lock()

    async def allow_request(self) -> bool:
        """Check if request is allowed under rate limit."""
        async with self.lock:
            now = datetime.now()
            cutoff = now - timedelta(minutes=1)

            # Remove old requests
            self.requests = [r for r in self.requests if r > cutoff]

            # Check limit
            if len(self.requests) >= self.max_requests:
                return False

            # Add new request
            self.requests.append(now)
            return True

    def reset(self) -> None:
        """Reset rate limiter."""
        self.requests = []


class GPTOSSToolOrchestrator(Plugin):
    """Plugin that orchestrates native GPT-OSS tools within Entity workflows.

    This plugin:
    - Enables browser and Python tools for GPT-OSS
    - Maintains sandboxing and security
    - Supports tool chaining for multi-step workflows
    - Implements rate limiting and resource constraints
    - Integrates with Entity's SandboxedToolRunner
    - Uses harmony format for tool configuration
    """

    supported_stages = [WorkflowExecutor.DO]
    dependencies = ["llm", "memory", "sandbox"]

    class ConfigModel(BaseModel):
        """Configuration for the tool orchestrator plugin."""

        # Tool enablement
        enable_browser_tool: bool = Field(
            default=True, description="Enable browser tool"
        )
        enable_python_tool: bool = Field(default=True, description="Enable Python tool")
        enable_tool_chaining: bool = Field(
            default=True, description="Enable multi-step tool workflows"
        )

        # Security settings
        default_execution_mode: ToolExecutionMode = Field(
            default=ToolExecutionMode.SANDBOXED,
            description="Default execution mode for tools",
        )
        require_user_approval: bool = Field(
            default=False,
            description="Require user approval for tool execution",
        )
        max_chain_length: int = Field(
            default=5, description="Maximum steps in tool chain", ge=1, le=10
        )

        # Rate limiting
        global_rate_limit_per_minute: int = Field(
            default=20, description="Global rate limit across all tools", ge=1, le=100
        )
        per_tool_rate_limits: Dict[str, int] = Field(
            default_factory=lambda: {"browser": 10, "python": 15},
            description="Per-tool rate limits",
        )

        # Resource constraints
        max_total_execution_time_ms: int = Field(
            default=120000,
            description="Maximum total execution time",
            ge=1000,
            le=600000,
        )
        max_parallel_tools: int = Field(
            default=3, description="Maximum parallel tool executions", ge=1, le=10
        )

        # Logging
        log_tool_invocations: bool = Field(
            default=True, description="Log all tool invocations"
        )
        log_tool_results: bool = Field(default=True, description="Log tool results")
        store_execution_history: bool = Field(
            default=True, description="Store execution history in memory"
        )

    def __init__(self, resources: dict[str, Any], config: Dict[str, Any] | None = None):
        """Initialize the tool orchestrator plugin."""
        super().__init__(resources, config)

        # Validate configuration
        validation_result = self.validate_config()
        if not validation_result.success:
            raise ValueError(f"Invalid configuration: {validation_result.errors}")

        # Initialize tools
        self.tools = {}
        if self.config.enable_browser_tool:
            self.tools["browser"] = BrowserTool()

        if self.config.enable_python_tool:
            self.tools["python"] = PythonTool()

        # Initialize rate limiter
        self.global_rate_limiter = RateLimiter(self.config.global_rate_limit_per_minute)

        # Track active executions
        self.active_executions = {}
        self.execution_history = []

    async def _execute_impl(self, context) -> str:
        """Execute tool orchestration in DO stage."""
        try:
            # Parse tool invocation from message
            invocations = await self._parse_tool_invocations(context.message)

            if not invocations:
                # No tool invocations detected, pass through
                return context.message

            # Check if chaining is required
            if len(invocations) > 1 and self.config.enable_tool_chaining:
                result = await self._execute_tool_chain(context, invocations)
            else:
                # Execute single tool
                result = await self._execute_single_tool(context, invocations[0])

            # Format and return result
            return await self._format_tool_result(result, context)

        except Exception as e:
            # Log error and return error message
            await context.log(
                level="error",
                category="tool_orchestrator",
                message=f"Tool orchestration error: {str(e)}",
                error=str(e),
            )
            return f"Tool execution failed: {str(e)}"

    async def _parse_tool_invocations(self, message: str) -> List[ToolInvocation]:
        """Parse tool invocations from message."""
        invocations = []

        # Look for tool invocation patterns in harmony format
        # Pattern: <tool:name>{parameters}</tool>
        tool_pattern = r"<tool:(\w+)>(.*?)</tool>"
        matches = re.finditer(tool_pattern, message, re.DOTALL)

        for match in matches:
            tool_name = match.group(1)
            params_str = match.group(2)

            try:
                # Parse parameters as JSON
                parameters = json.loads(params_str)
            except json.JSONDecodeError:
                # Try to parse as simple key-value pairs
                parameters = self._parse_simple_params(params_str)

            invocation = ToolInvocation(
                tool_name=tool_name,
                parameters=parameters,
                correlation_id=f"{tool_name}_{int(time.time() * 1000)}",
            )
            invocations.append(invocation)

        return invocations

    def _parse_simple_params(self, params_str: str) -> Dict[str, Any]:
        """Parse simple parameter format."""
        params = {}
        lines = params_str.strip().split("\n")
        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                params[key.strip()] = value.strip()
        return params

    async def _execute_single_tool(
        self, context, invocation: ToolInvocation
    ) -> ToolResult:
        """Execute a single tool invocation."""
        tool_name = invocation.tool_name

        if tool_name not in self.tools:
            return ToolResult(
                tool_name=tool_name,
                correlation_id=invocation.correlation_id,
                status=ToolStatus.FAILED,
                error=f"Unknown tool: {tool_name}",
            )

        # Check global rate limit
        if not await self.global_rate_limiter.allow_request():
            return ToolResult(
                tool_name=tool_name,
                correlation_id=invocation.correlation_id,
                status=ToolStatus.RATE_LIMITED,
                error="Global rate limit exceeded",
            )

        # Get sandbox if available
        sandbox = (
            context.get_resource("sandbox")
            if hasattr(context, "get_resource")
            else None
        )

        # Execute tool
        tool = self.tools[tool_name]
        result = await tool.execute(invocation.parameters, sandbox)

        # Log execution
        if self.config.log_tool_invocations:
            await self._log_tool_execution(context, invocation, result)

        # Store in history
        if self.config.store_execution_history:
            await self._store_execution_history(context, invocation, result)

        return result

    async def _execute_tool_chain(
        self, context, invocations: List[ToolInvocation]
    ) -> List[ToolResult]:
        """Execute a chain of tool invocations."""
        if len(invocations) > self.config.max_chain_length:
            raise ValueError(
                f"Tool chain too long: {len(invocations)} > {self.config.max_chain_length}"
            )

        results = []
        total_start_time = time.time()

        for invocation in invocations:
            # Check total execution time
            elapsed_ms = (time.time() - total_start_time) * 1000
            if elapsed_ms > self.config.max_total_execution_time_ms:
                # Timeout for remaining tools
                results.append(
                    ToolResult(
                        tool_name=invocation.tool_name,
                        correlation_id=invocation.correlation_id,
                        status=ToolStatus.TIMEOUT,
                        error="Chain execution timeout",
                    )
                )
                continue

            # Execute tool
            result = await self._execute_single_tool(context, invocation)
            results.append(result)

            # If tool failed, optionally stop chain
            if result.status == ToolStatus.FAILED:
                break

        return results

    async def _format_tool_result(
        self, result: ToolResult | List[ToolResult], context
    ) -> str:
        """Format tool results for output."""
        if isinstance(result, list):
            # Format multiple results
            formatted = []
            for r in result:
                formatted.append(self._format_single_result(r))
            return "\n\n".join(formatted)
        else:
            return self._format_single_result(result)

    def _format_single_result(self, result: ToolResult) -> str:
        """Format a single tool result."""
        if result.status == ToolStatus.COMPLETED:
            return f"[{result.tool_name}]: {json.dumps(result.result, indent=2)}"
        else:
            return f"[{result.tool_name}]: Error - {result.error}"

    async def _log_tool_execution(
        self, context, invocation: ToolInvocation, result: ToolResult
    ) -> None:
        """Log tool execution details."""
        await context.log(
            level="info",
            category="tool_orchestrator",
            message=f"Tool executed: {invocation.tool_name}",
            tool_name=invocation.tool_name,
            correlation_id=invocation.correlation_id,
            status=result.status.value,
            execution_time_ms=result.execution_time_ms,
            parameters=invocation.parameters if self.config.log_tool_results else None,
            result=result.result if self.config.log_tool_results else None,
        )

    async def _store_execution_history(
        self, context, invocation: ToolInvocation, result: ToolResult
    ) -> None:
        """Store execution history in memory."""
        history_entry = {
            "timestamp": invocation.timestamp.isoformat(),
            "tool_name": invocation.tool_name,
            "correlation_id": invocation.correlation_id,
            "parameters": invocation.parameters,
            "status": result.status.value,
            "execution_time_ms": result.execution_time_ms,
            "result": result.result if result.status == ToolStatus.COMPLETED else None,
            "error": result.error if result.status == ToolStatus.FAILED else None,
        }

        # Add to local history
        self.execution_history.append(history_entry)

        # Store in memory
        await context.remember(
            f"tool_execution:{invocation.correlation_id}", history_entry
        )

    # Public API methods

    def get_available_tools(self) -> List[str]:
        """Get list of available tools."""
        return list(self.tools.keys())

    def get_tool_config(self, tool_name: str) -> Optional[ToolConfig]:
        """Get configuration for a specific tool."""
        if tool_name in self.tools:
            return self.tools[tool_name].config
        return None

    async def execute_tool(
        self, tool_name: str, parameters: Dict[str, Any], context: Optional[Any] = None
    ) -> ToolResult:
        """Execute a tool programmatically."""
        invocation = ToolInvocation(
            tool_name=tool_name,
            parameters=parameters,
            correlation_id=f"{tool_name}_{int(time.time() * 1000)}",
        )

        if context:
            return await self._execute_single_tool(context, invocation)
        else:
            # Execute without context
            if tool_name not in self.tools:
                return ToolResult(
                    tool_name=tool_name,
                    correlation_id=invocation.correlation_id,
                    status=ToolStatus.FAILED,
                    error=f"Unknown tool: {tool_name}",
                )

            tool = self.tools[tool_name]
            return await tool.execute(parameters)

    def get_harmony_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get all tool definitions in harmony format."""
        definitions = []
        for tool in self.tools.values():
            definitions.append(tool.get_harmony_format())
        return definitions

    async def reset_rate_limits(self) -> None:
        """Reset all rate limits."""
        self.global_rate_limiter.reset()
        for tool in self.tools.values():
            if hasattr(tool, "rate_limiter"):
                tool.rate_limiter.reset()

    async def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        stats = {
            "total_executions": len(self.execution_history),
            "by_tool": {},
            "by_status": {},
            "average_execution_time_ms": 0,
        }

        if self.execution_history:
            total_time = 0
            for entry in self.execution_history:
                # By tool
                tool = entry["tool_name"]
                stats["by_tool"][tool] = stats["by_tool"].get(tool, 0) + 1

                # By status
                status = entry["status"]
                stats["by_status"][status] = stats["by_status"].get(status, 0) + 1

                # Total time
                total_time += entry.get("execution_time_ms", 0)

            stats["average_execution_time_ms"] = total_time / len(
                self.execution_history
            )

        return stats
