import asyncio
import importlib.util
import logging
import os
from functools import wraps
from inspect import isclass, signature, Parameter
from typing import Any, Callable, Dict, List, Optional, Type

from langchain_core.tools import StructuredTool
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class BaseToolPlugin:
    name: str
    description: str
    args_schema: Type[BaseModel]

    async def run(self, input_data: BaseModel) -> Any:
        raise NotImplementedError


class FunctionTool:
    def __init__(self, func: Callable, args_schema: Type[BaseModel]):
        self.func = func
        self.args_schema = args_schema
        self.name = func.__name__
        self.description = func.__doc__ or "No description provided."

    def to_langchain_tool(self) -> StructuredTool:
        @wraps(self.func)
        async def safe_func(input_data: BaseModel):
            try:
                return await self.func(input_data)
            except Exception as e:
                logger.exception(f"❌ Tool '{self.name}' failed")
                return f"[Tool Error: {self.name}] {str(e)}"

        return StructuredTool.from_function(
            ToolManager.sync_adapter(safe_func),
            name=self.name,
            description=self.description,
            args_schema=self.args_schema,
        )


class ToolManager:
    def __init__(self):
        self._tools: Dict[str, Any] = {}
        self._langchain_tools: List[Any] = []

    @classmethod
    def setup(cls, plugin_directory: str) -> "ToolManager":
        manager = cls()
        manager.load_plugins_from_config(plugin_directory)
        return manager

    @staticmethod
    def sync_adapter(async_func: Callable) -> Callable:
        @wraps(async_func)
        def wrapper(input_data: BaseModel):
            import concurrent.futures

            loop = asyncio.new_event_loop()
            coro = async_func(input_data)

            if not asyncio.iscoroutine(coro):
                raise TypeError("Expected coroutine from async_func")

            with concurrent.futures.ThreadPoolExecutor() as executor:
                return executor.submit(loop.run_until_complete, coro).result()

        return wrapper

    def register_function(self, tool_func: Callable, args_schema: Type[BaseModel]):
        tool = FunctionTool(tool_func, args_schema).to_langchain_tool()
        self._tools[tool.name] = tool
        self._langchain_tools.append(tool)
        logger.info(f"✅ Registered function tool: {tool.name}")

    def register_class(self, cls: Type[BaseToolPlugin]):
        if not issubclass(cls, BaseToolPlugin):
            raise TypeError(
                f"Tool class {cls.__name__} must inherit from BaseToolPlugin"
            )

        instance = cls()

        # Validate run() signature: one argument after self, matching args_schema
        run_sig = signature(cls.run)
        params = list(run_sig.parameters.values())
        positional_params = [
            p
            for p in params
            if p.kind in (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD)
        ]

        if len(positional_params) != 2:
            raise TypeError(
                f"run() method of {cls.__name__} must take exactly one argument besides self"
            )

        input_param_type = positional_params[1].annotation
        if input_param_type is Parameter.empty or input_param_type != cls.args_schema:
            raise TypeError(
                f"run() method of {cls.__name__} must take a single argument of type {cls.args_schema.__name__}, got {input_param_type}"
            )

        async def wrapped(input_data: Any):
            try:
                if isinstance(input_data, str):
                    key = list(instance.args_schema.model_fields.keys())[0]
                    input_data = {key: input_data}

                if not isinstance(input_data, instance.args_schema):
                    input_data = instance.args_schema(**input_data)
                    result = await instance.run(input_data)
                    if result is None:
                        raise ValueError(f"Tool '{instance.name}' returned None")
                    if not isinstance(result, str):
                        raise TypeError(
                            f"Tool '{instance.name}' must return a string, got: {type(result)}"
                        )
                    return result

            except Exception as e:
                logger.exception(f"❌ Error in tool '{instance.name}'")
                return f"[Tool Error: {instance.name}] {str(e)}"

        tool = StructuredTool.from_function(
            self.sync_adapter(wrapped),
            name=instance.name,
            description=instance.description,
            args_schema=instance.args_schema,
        )

        self._tools[instance.name] = tool
        self._langchain_tools.append(tool)
        logger.info(f"✅ Registered plugin tool: {instance.name}")

    def load_plugins_from_config(self, directory: str):
        if not os.path.isdir(directory):
            logger.error(f"❌ Plugin directory does not exist: {directory}")
            return

        for filename in os.listdir(directory):
            if filename.endswith(".py"):
                self.load_plugin_file(os.path.join(directory, filename))

    def load_plugin_file(self, file_path: str):
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
                try:
                    self.register_class(obj)
                    registered += 1
                except Exception:
                    logger.exception(
                        f"❌ Failed to register tool class: {obj.__name__}"
                    )

        if registered == 0:
            logger.warning(f"⚠️ No tools registered from plugin file: {file_path}")
        else:
            logger.info(f"🔌 Registered {registered} tool(s) from: {file_path}")

    def get_tool(self, name: str) -> Optional[Any]:
        return self._tools.get(name)

    def get_all_tools(self) -> List[Any]:
        return self._langchain_tools

    def list_tool_names(self) -> List[str]:
        return list(self._tools.keys())
