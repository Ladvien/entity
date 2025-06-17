from ..tool_registry import tool_registry

def store_memory_factory(ctx):
    memory_system = ctx["memory_system"]

    def store_memory(content: str, memory_type: str = "important", thread_id: str = "default") -> str:
        try:
            memory_system.store(content, memory_type, thread_id)
            return f"Stored: {content[:50]}..."
        except Exception as e:
            return f"Failed to store memory: {e}"

    return store_memory

def recall_memory_factory(ctx):
    memory_system = ctx["memory_system"]

    def recall_memory(query: str, thread_id: str = "default") -> str:
        try:
            return memory_system.recall(query, thread_id)
        except Exception as e:
            return f"Failed to recall memory: {e}"

    return recall_memory

def register_memory_tools():
    tool_registry.register_factory(store_memory_factory)
    tool_registry.register_factory(recall_memory_factory)
