import asyncio
import importlib.util
import logging
import os
from functools import wraps
from inspect import isclass, signature, Parameter
from typing import Any, Callable, Dict, List, Optional, Type

from langchain_core.tools import StructuredTool
from pydantic import BaseModel

from src.tools.base_tool_plugin import BaseToolPlugin
from plugins import PLUGIN_TOOLS

logger = logging.getLogger(__name__)


class ToolUsageTracker:
    _instance = None
    _usage_count = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._usage_count = {}
        return cls._instance

    def increment(self, tool_name: str) -> int:
        self._usage_count[tool_name] = self._usage_count.get(tool_name, 0) + 1
        return self._usage_count[tool_name]

    def reset(self):
        self._usage_count.clear()
        logger.debug("🔄 Tool usage tracker reset")

    def get_total_usage(self) -> int:
        return sum(self._usage_count.values())

    def get_usage(self, tool_name: str) -> int:
        return self._usage_count.get(tool_name, 0)


class SelfLimitingTool:
    def __init__(self, tool, max_uses_per_tool=2, max_total_tools=4):
        self.tool = tool
        self.max_uses_per_tool = max_uses_per_tool
        self.max_total_tools = max_total_tools
        self.tracker = ToolUsageTracker()

        self.name = tool.name
        self.description = f"{tool.description} (Max {max_uses_per_tool} uses)"
        self.args_schema = getattr(tool, "args_schema", None)

    def __getattr__(self, name):
        return getattr(self.tool, name)

    def run(self, *args, **kwargs):
        return self._execute(self.tool.run, *args, **kwargs)

    async def arun(self, *args, **kwargs):
        if hasattr(self.tool, "arun"):
            return await self._execute(self.tool.arun, *args, **kwargs)
        return await self._execute(self.tool.run, *args, **kwargs)

    def _execute(self, tool_func, *args, **kwargs):
        total_usage = self.tracker.get_total_usage()
        if total_usage >= self.max_total_tools:
            logger.warning(f"🛑 Max total tool usage reached ({self.max_total_tools})")
            return f"Maximum tool usage reached. Limit: {self.max_total_tools}."

        current_usage = self.tracker.get_usage(self.name)
        if current_usage >= self.max_uses_per_tool:
            logger.warning(
                f"🛑 Tool '{self.name}' usage limit reached ({self.max_uses_per_tool})"
            )
            return f"Tool '{self.name}' usage limit reached."

        self.tracker.increment(self.name)

        try:
            if asyncio.iscoroutinefunction(tool_func):
                return asyncio.create_task(tool_func(*args, **kwargs))
            result = tool_func(*args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"❌ Tool '{self.name}' execution failed: {e}")
            return f"Tool '{self.name}' error: {e}"


class ToolManager:
    def __init__(self):
        self._tools: Dict[str, Any] = {}
        self._langchain_tools: List[Any] = []
        self.tracker = ToolUsageTracker()

    def register(self, tool: BaseToolPlugin):
        self.register_class(tool.__class__)

    @classmethod
    def setup(cls, plugin_directory: str, enabled_tools: List[str] = None):
        manager = cls()
        for tool_cls in PLUGIN_TOOLS:
            if enabled_tools is None or tool_cls.name in enabled_tools:
                manager.register(tool_cls())
        return manager

    @staticmethod
    def sync_adapter(async_func: Callable) -> Callable:
        @wraps(async_func)
        def wrapper(input_data: BaseModel):
            try:
                # Already in event loop? Schedule it
                loop = asyncio.get_running_loop()
                future = loop.create_task(async_func(input_data))
                return loop.run_until_complete(future)
            except RuntimeError:
                # Not in async context — safe to run fresh loop
                return asyncio.run(async_func(input_data))

        return wrapper

    def register_function(self, tool_func: Callable, args_schema: Type[BaseModel]):
        tool = StructuredTool.from_function(
            self.sync_adapter(tool_func),
            name=tool_func.__name__,
            description=tool_func.__doc__ or "",
            args_schema=args_schema,
        )
        self._tools[tool.name] = tool
        self._langchain_tools.append(tool)
        logger.info(f"✅ Registered function tool: {tool.name}")

    def register_class(self, cls: Type[BaseToolPlugin]):
        if not issubclass(cls, BaseToolPlugin):
            raise TypeError(f"{cls.__name__} must inherit from BaseToolPlugin")

        instance = cls()
        run_sig = signature(cls.run)
        params = list(run_sig.parameters.values())
        positional = [
            p
            for p in params
            if p.kind in (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD)
        ]

        if len(positional) != 2:
            raise TypeError(f"{cls.__name__}.run() must take one argument besides self")

        if not hasattr(cls, "args_schema") or cls.args_schema is None:
            raise TypeError(f"{cls.__name__} is missing required args_schema")

        if positional[1].annotation != cls.args_schema:
            raise TypeError(
                f"{cls.__name__}.run() must take {cls.args_schema.__name__}, got {positional[1].annotation}"
            )

        async def wrapped(input_data: Any):
            try:
                if isinstance(input_data, str):
                    key = list(instance.args_schema.model_fields.keys())[0]
                    input_data = {key: input_data}
                if not isinstance(input_data, instance.args_schema):
                    input_data = instance.args_schema(**input_data)
                result = await instance.run(input_data)
                if not isinstance(result, str):
                    raise TypeError(
                        f"{instance.name} must return str, got {type(result)}"
                    )
                return result
            except Exception as e:
                logger.exception(f"❌ Error in tool '{instance.name}'")
                return f"[Tool Error: {instance.name}] {e}"

        tool = StructuredTool(
            name=instance.name,
            description=instance.description,
            args_schema=instance.args_schema,
            coroutine=wrapped,  # ✅ async coroutine explicitly set
        )

        self._tools[instance.name] = tool
        self._langchain_tools.append(tool)
        logger.info(f"✅ Registered plugin tool: {instance.name}")

    def load_plugins_from_config(
        self, directory: str, enabled_tools: Optional[List[str]] = None
    ):
        if not os.path.isdir(directory):
            logger.error(f"❌ Plugin directory does not exist: {directory}")
            return

        for filename in os.listdir(directory):
            if filename.endswith(".py"):
                self.load_plugin_file(os.path.join(directory, filename), enabled_tools)

    def load_plugin_file(
        self, file_path: str, enabled_tools: Optional[List[str]] = None
    ):
        try:
            module_name = os.path.splitext(os.path.basename(file_path))[0]
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if not spec or not spec.loader:
                raise ImportError(f"Invalid spec or loader for {file_path}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception:
            logger.exception(f"❌ Failed to load plugin module: {file_path}")
            return

        registered = 0
        for name in dir(module):
            obj = getattr(module, name)
            if (
                isclass(obj)
                and issubclass(obj, BaseToolPlugin)
                and obj is not BaseToolPlugin
            ):
                plugin_name = getattr(obj, "name", None)
                if enabled_tools and plugin_name not in enabled_tools:
                    logger.info(f"🔒 Skipping disabled tool: {plugin_name}")
                    continue
                try:
                    self.register_class(obj)
                    registered += 1
                except Exception:
                    logger.exception(f"❌ Failed to register: {obj.__name__}")

        if registered == 0:
            logger.warning(f"⚠️ No tools registered from: {file_path}")
        else:
            logger.info(f"🔌 Registered {registered} tool(s) from: {file_path}")

    def get_tool(self, name: str) -> Optional[Any]:
        return self._tools.get(name)

    def get_all_tools(self) -> List[Any]:
        self.tracker.reset()
        return self._langchain_tools

    def list_tool_names(self) -> List[str]:
        return list(self._tools.keys())

    def reset_usage(self):
        self.tracker.reset()
        logger.info("🔄 Tool usage counters reset")
