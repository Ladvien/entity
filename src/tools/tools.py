import asyncio
import logging
import ast
import operator
from functools import wraps
from inspect import signature, Signature
from typing import Dict, Any, List, Optional, Callable

from langchain_core.tools import StructuredTool, BaseTool
from pydantic import BaseModel, Field

from src.tools.memory import MemorySearchInput, VectorMemorySystem

logger = logging.getLogger(__name__)


class QueryInput(BaseModel):
    query: str = Field(..., description="The search query")
    thread_id: str = Field(default="default", description="Conversation thread ID")


class MemoryInput(BaseModel):
    content: str = Field(..., description="The content to store")
    importance: float = Field(default=0.8, description="Importance score")


# --- Helpers ---


def safe_tool_wrapper(tool_func: Callable) -> Callable:
    """Wrap a tool function to catch and log exceptions cleanly"""
    try:
        sig: Optional[Signature] = signature(tool_func)
    except ValueError:
        sig = None

    param = next(iter(sig.parameters.values()), None) if sig else None
    param_type = param.annotation if param else None
    expects_model = (
        param_type
        and isinstance(param_type, type)
        and issubclass(param_type, BaseModel)
    )

    @wraps(tool_func)
    async def wrapped(*args, **kwargs):
        try:
            if len(args) > 1:
                raise ValueError(
                    f"Too many positional arguments for tool '{tool_func.__name__}'"
                )

            input_arg = args[0] if args else kwargs

            if expects_model:
                if isinstance(input_arg, param_type):
                    model_input = input_arg
                elif isinstance(input_arg, dict):
                    model_input = param_type(**input_arg)
                elif isinstance(input_arg, str):
                    fields = param_type.__fields__
                    if "query" in fields:
                        model_input = param_type(query=input_arg)
                    elif "content" in fields:
                        model_input = param_type(content=input_arg)
                    else:
                        raise ValueError(
                            f"Cannot coerce string to {param_type.__name__}: no suitable fields"
                        )
                else:
                    raise ValueError(f"Unsupported input type: {type(input_arg)}")
                result = await tool_func(model_input)
            else:
                result = await tool_func(*args, **kwargs)

            logger.debug(f"✅ Tool '{tool_func.__name__}' result: {result}")
            return result
        except Exception as e:
            logger.exception(f"❌ Tool '{tool_func.__name__}' failed")
            return f"[Tool Error: {tool_func.__name__}] {str(e)}"

    return wrapped


def ensure_event_loop():
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


def sync_adapter(async_func: Callable) -> Callable:
    """Adapter to run async tool functions from sync contexts (e.g., LangChain tools)"""

    @wraps(async_func)
    def wrapper(*args, **kwargs):
        loop = ensure_event_loop()
        return loop.run_until_complete(async_func(*args, **kwargs))

    return wrapper


# --- Registry ---


class ToolRegistry:
    """Tool registry with memory context"""

    def __init__(self):
        self._tools: Dict[str, Any] = {}
        self._langchain_tools: List[Any] = []
        self.memory_system: Optional[VectorMemorySystem] = None

    def set_memory_system(self, memory_system: VectorMemorySystem):
        self.memory_system = memory_system

    def register(
        self,
        tool_func: Callable,
        name: Optional[str] = None,
        args_schema: Optional[BaseModel] = None,
    ):
        if isinstance(tool_func, BaseTool):
            lc_tool = tool_func
        else:
            wrapped_func = safe_tool_wrapper(tool_func)
            lc_tool = StructuredTool.from_function(
                sync_adapter(wrapped_func),
                name=name or tool_func.__name__,
                description=tool_func.__doc__ or "No description provided.",
                args_schema=args_schema,
            )

        tool_name = name or lc_tool.name
        self._tools[tool_name] = lc_tool
        self._langchain_tools.append(lc_tool)

        logger.info(f"✅ Registered tool: {tool_name}")
        logger.debug(
            f"🔧 StructuredTool created: name={lc_tool.name}, description={lc_tool.description}"
        )

    def get_tool(self, name: str) -> Optional[Any]:
        return self._tools.get(name)

    def get_all_tools(self) -> List[Any]:
        return self._langchain_tools

    def list_tool_names(self) -> List[str]:
        return list(self._tools.keys())


# --- Tool Implementations ---


async def web_search_tool(query: str) -> str:
    """
    Search the web for information (mock).
    """
    return f"Web search results for '{query}': No results found (mock implementation)"


async def calculator_tool(expression: str) -> str:
    """
    Calculate the result of a basic math expression.
    """
    try:
        allowed_ops = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
        }

        def eval_expr(node):
            if isinstance(node, ast.Constant):
                return node.value
            elif isinstance(node, ast.BinOp):
                return allowed_ops[type(node.op)](
                    eval_expr(node.left), eval_expr(node.right)
                )
            elif isinstance(node, ast.UnaryOp):
                return allowed_ops[type(node.op)](eval_expr(node.operand))
            raise TypeError(f"Unsupported node: {node}")

        tree = ast.parse(expression, mode="eval")
        return f"{expression} = {eval_expr(tree.body)}"

    except Exception as e:
        logger.exception("Calculator tool failed")
        return f"Cannot calculate '{expression}': {e}"


# --- Memory Tool Creators ---


def create_memory_tools(registry: ToolRegistry):

    @safe_tool_wrapper
    async def search_memories(input: MemorySearchInput):
        """
        Search vector memory for relevant past content.
        """
        if registry.memory_system:
            results = await registry.memory_system.search_memory(
                input.query, input.thread_id, k=5
            )
            if results:
                return "\n\n".join([f"Memory: {doc.page_content}" for doc in results])
            return "No relevant memories found."
        return "Memory system not available."

    async def store_important_memory(input: MemoryInput) -> str:
        """
        Store an important memory in the vector database.
        """
        if registry.memory_system:
            await registry.memory_system.add_memory(
                thread_id="default",
                content=input.content,
                memory_type="important",
                importance_score=input.importance,
                emotional_tone="neutral",
            )
            return f"Stored in memory: {input.content[:100]}..."
        return "Memory system not available."

    return search_memories, store_important_memory


# --- Setup ---


async def setup_tools(
    config: Dict[str, Any], memory_system: VectorMemorySystem
) -> ToolRegistry:
    registry = ToolRegistry()
    registry.set_memory_system(memory_system)

    if "web_search" in config.enabled:
        registry.register(web_search_tool, args_schema=QueryInput)

    if "calculator" in config.enabled:
        registry.register(calculator_tool)

    if "memory_search" in config.enabled or "store_memory" in config.enabled:
        search_tool, store_tool = create_memory_tools(registry)

        if "memory_search" in config.enabled:
            registry.register(
                search_tool, name="search_memories", args_schema=QueryInput
            )

        if "store_memory" in config.enabled:
            registry.register(
                store_tool, name="store_important_memory", args_schema=MemoryInput
            )

    logger.info(f"🔧 Tool setup complete with tools: {registry.list_tool_names()}")
    return registry
