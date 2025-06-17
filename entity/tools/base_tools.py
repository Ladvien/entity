from ..tool_registry import tool_registry

@tool_registry.register
def calculator(expression: str) -> str:
    """A simple calculator tool"""
    try:
        result = eval(expression)
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {e}"
