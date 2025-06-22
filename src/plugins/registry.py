import asyncio
import importlib.util
import logging
import os
from functools import wraps
from inspect import isclass, signature, Parameter
from typing import Any, Callable, Dict, List, Optional, Type

from langchain_core.tools import StructuredTool
from pydantic import BaseModel


from src.plugins.base import BaseToolPlugin
from src.core.config import (
    ToolConfig,
)

logger = logging.getLogger(__name__)


class ToolUsageTracker:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._usage_count = {}
            cls._limits = {}  # tool_name → max_uses (simplified)
            cls._global_limit = None  # NEW: Global limit
        return cls._instance

    def set_global_limit(self, max_total: int):
        """Set the global tool usage limit"""
        self._global_limit = max_total
        print(f"🔧 DEBUG: Setting global tool limit: {max_total}")

    def set_limit(self, tool_name: str, max_uses: int):
        """Set per-tool usage limit (simplified signature)"""
        print(f"🔧 DEBUG: Setting limit for '{tool_name}': max_uses={max_uses}")
        self._limits[tool_name] = max_uses

    def increment(self, tool_name: str) -> int:
        self._usage_count[tool_name] = self._usage_count.get(tool_name, 0) + 1
        return self._usage_count[tool_name]

    def check_limit(self, tool_name: str) -> bool:
        """Check if a specific tool can still be used"""
        # Check global limit first (account for the pending increment)
        if (
            self._global_limit is not None
            and self.get_total_usage() + 1
            > self._global_limit  # +1 for this pending call
        ):
            print(
                f"🚫 DEBUG: Global limit would be exceeded! Current: {self.get_total_usage()}, Limit: {self._global_limit}"
            )
            return False

        # Check per-tool limit
        usage = self._usage_count.get(tool_name, 0)
        max_uses = self._limits.get(tool_name)
        if max_uses is not None and usage >= max_uses:
            print(
                f"🚫 DEBUG: Tool '{tool_name}' individual limit hit! Usage: {usage}, Limit: {max_uses}"
            )
            return False

        return True

    def any_tools_available(self) -> bool:
        """Check if any tools are still available"""
        # If global limit is hit, no tools available
        if (
            self._global_limit is not None
            and self.get_total_usage() >= self._global_limit
        ):
            return False

        # Check if any individual tool has uses left
        return any(self.check_limit(tool_name) for tool_name in self._limits.keys())

    def reset(self):
        self._usage_count.clear()

    def get_total_usage(self) -> int:
        return sum(self._usage_count.values())


class ToolManager:
    def __init__(self, config: Optional[ToolConfig] = None):
        self._tools: Dict[str, Any] = {}
        self._langchain_tools: List[Any] = []
        self.tracker = ToolUsageTracker()
        self.config = config

    def register(self, tool: BaseToolPlugin):
        self.register_class(tool.__class__)

    @classmethod
    def setup(cls, plugin_directory: str, config: ToolConfig):
        manager = cls(config)
        manager.load_plugins_from_config(
            plugin_directory,
            [t.name for t in config.enabled] if config.enabled else None,
        )
        return manager

    @staticmethod
    def sync_adapter(async_func: Callable) -> Callable:
        @wraps(async_func)
        def wrapper(input_data: BaseModel):
            try:
                loop = asyncio.get_running_loop()
                future = loop.create_task(async_func(input_data))
                return loop.run_until_complete(future)
            except RuntimeError:
                return asyncio.run(async_func(input_data))

        return wrapper

    def register_function(self, tool_func: Callable, args_schema: Type[BaseModel]):
        tool = StructuredTool(
            name=tool_func.__name__,
            description=tool_func.__doc__ or "",
            args_schema=args_schema,
            func=self.sync_adapter(tool_func),
        )
        self._tools[tool.name] = tool
        self._langchain_tools.append(tool)
        logger.info(f"✅ Registered function tool: {tool.name}")

    def register_class(self, cls: Type[BaseToolPlugin]):
        if not issubclass(cls, BaseToolPlugin):
            raise TypeError(f"{cls.__name__} must inherit from BaseToolPlugin")

        instance = cls()

        # Ensure the tool implements necessary methods for limiting

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

        # Now use the helper function to handle tool wrapping
        wrapped_tool_function = self._create_wrapped_tool_function(instance)

        # Register the tool and apply limits
        tool = StructuredTool(
            name=instance.name,
            description=instance.description,
            args_schema=instance.args_schema,
            coroutine=wrapped_tool_function,
        )
        self._tools[instance.name] = tool
        self._langchain_tools.append(tool)
        logger.info(f"✅ Registered plugin tool: {instance.name}")

    def any_tools_available(self) -> bool:
        """Check if any tools are still available"""
        return any(self.check_limit(tool_name) for tool_name in self._limits.keys())

    def _create_wrapped_tool_function(self, instance: BaseToolPlugin):
        """Helper function to wrap tool execution with limit checks"""

        async def wrapped(input_data: Any):
            try:
                print(
                    f"🔍 DEBUG: Tool '{instance.name}' called. Current usage: {self.tracker._usage_count.get(instance.name, 0)}"
                )

                # Check tool usage limit
                if not self.tracker.check_limit(instance.name):
                    print(f"❌ DEBUG: Tool '{instance.name}' hit limit!")

                    # NEW: Check if ALL tools are exhausted
                    if not self.tracker.any_tools_available():
                        return "All available tools have reached their usage limits. Please provide a final answer without using any tools."

                    return f"Tool '{instance.name}' has reached its usage limit."

                print(f"✅ DEBUG: Tool '{instance.name}' allowed, incrementing")
                self.tracker.increment(instance.name)
                print(
                    f"📊 DEBUG: New usage count: {self.tracker._usage_count.get(instance.name, 0)}"
                )

                # Ensure input data is correctly structured
                if isinstance(input_data, str):
                    key = list(instance.args_schema.model_fields.keys())[0]
                    input_data = {key: input_data}
                if not isinstance(input_data, instance.args_schema):
                    input_data = instance.args_schema(**input_data)

                # Run the tool's actual logic
                result = await instance.run(input_data)

                # Ensure the result is a string
                if not isinstance(result, str):
                    result = str(result)

                return result

            except Exception as e:
                logger.exception(f"❌ Tool '{instance.name}' execution failed: {e}")
                return f"Tool '{instance.name}' failed: {str(e)}"

        return wrapped

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

        # ✅ Set global limit once per file loading (only if config exists)
        if (
            self.config
            and hasattr(self.config, "max_total_tool_uses")
            and not hasattr(self.tracker, "_global_limit_set")
        ):
            self.tracker.set_global_limit(self.config.max_total_tool_uses)
            self.tracker._global_limit_set = True  # Prevent setting it multiple times

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

                # ✅ Set per-tool limits from config
                if self.config and self.config.enabled:
                    tool_cfg = next(
                        (
                            t
                            for t in self.config.enabled
                            if getattr(t, "name", t.get("name")) == plugin_name
                        ),
                        None,
                    )
                    if tool_cfg:
                        max_uses = getattr(
                            tool_cfg, "max_uses", tool_cfg.get("max_uses")
                        )
                        self.tracker.set_limit(
                            plugin_name, max_uses
                        )  # Only pass max_uses

                try:
                    # Register the tool
                    self.register_class(obj)
                    registered += 1
                except Exception as e:
                    logger.exception(
                        f"❌ Failed to register tool: {obj.__name__} with error: {e}"
                    )

        if registered == 0:
            logger.warning(f"⚠️ No tools registered from: {file_path}")
        else:
            logger.info(f"🔌 Registered {registered} tool(s) from: {file_path}")

    def get_tool(self, name: str) -> Optional[Any]:
        return self._tools.get(name)

    def get_all_tools(self) -> List[Any]:
        return self._langchain_tools

    def list_tool_names(self) -> List[str]:
        return list(self._tools.keys())

    def reset_usage(self):
        self.tracker.reset()
        logger.info("🔄 Tool usage counters reset")
