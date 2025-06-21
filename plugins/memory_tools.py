# plugins/memory_tools.py

import logging
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from src.core.registry import ServiceRegistry
from src.tools.base_tool_plugin import BaseToolPlugin

logger = logging.getLogger(__name__)

# -------------------------------
# 📥 Input Schemas
# -------------------------------


class MemorySearchInput(BaseModel):
    query: str = Field(..., description="Search query")
    thread_id: Optional[str] = Field(
        default="default", description="Conversation thread ID"
    )
    limit: Optional[int] = Field(default=5, description="Number of results to return")


class DeepMemorySearchTool(BaseToolPlugin):
    name = "deep_memory_search"
    description = (
        "Searches both stored vector memories and raw chat history for deep context"
    )
    args_schema = MemorySearchInput

    def get_context_injection(
        self, user_input: str, thread_id: str = "default"
    ) -> Dict[str, str]:
        return {
            "deep_memory_search_query": user_input,
            "deep_memory_search_thread_id": thread_id,
        }

    async def run(self, input_data: MemorySearchInput) -> str:
        memory_system = ServiceRegistry.try_get("memory_system")
        if not memory_system:
            return "❌ Memory system not available"

        results = await memory_system.deep_search(
            query=input_data.query,
            thread_id=input_data.thread_id,
            k=input_data.limit,
        )

        if not results:
            return f"No relevant results found for: {input_data.query}"

        return "\n".join(
            f"{i+1}. [{doc.metadata.get('source', 'unknown')}] {doc.page_content[:80]}..."
            for i, doc in enumerate(results)
        )


class StoreMemoryInput(BaseModel):
    content: str = Field(..., description="Memory content to store")
    thread_id: Optional[str] = Field(
        default="default", description="Conversation thread ID"
    )
    memory_type: Optional[str] = Field(
        default="observation", description="Type of memory (e.g. observation, summary)"
    )
    importance_score: Optional[float] = Field(
        default=0.5, description="Relevance of the memory"
    )


# -------------------------------
# 🧠 Vector Memory Tools
# -------------------------------


class MemorySearchTool(BaseToolPlugin):
    name = "memory_search"
    description = "Search stored memories using semantic similarity"
    args_schema = MemorySearchInput

    def get_context_injection(
        self, user_input: str, thread_id: str = "default"
    ) -> Dict[str, str]:
        return {
            "memory_search_query": user_input,
            "memory_search_thread_id": thread_id,
        }

    async def run(self, input_data: MemorySearchInput) -> str:
        memory_system = ServiceRegistry.try_get("memory_system")
        if not memory_system:
            return "❌ Vector memory system not available"

        results = await memory_system.search_memory(
            query=input_data.query,
            thread_id=input_data.thread_id,
            k=input_data.limit,
        )

        if not results:
            return f"No relevant memories found for: {input_data.query}"

        return "\n".join(
            f"{i+1}. [{doc.metadata.get('memory_type', 'unknown')}] {doc.page_content[:80]}..."
            for i, doc in enumerate(results)
        )


class StoreMemoryTool(BaseToolPlugin):
    name = "store_memory"
    description = "Store a memory entry for future reference"
    args_schema = StoreMemoryInput

    def get_context_injection(
        self, content: str, thread_id: str = "default", memory_type: str = "observation"
    ) -> Dict[str, Any]:
        return {
            "memory_store_content": content,
            "memory_store_thread_id": thread_id,
            "memory_store_type": memory_type,
        }

    async def run(self, input_data: StoreMemoryInput) -> str:
        memory_system = ServiceRegistry.try_get("memory_system")
        if not memory_system:
            return "❌ Vector memory system not available"

        await memory_system.add_memory(
            thread_id=input_data.thread_id,
            content=input_data.content,
            memory_type=input_data.memory_type,
            importance_score=input_data.importance_score,
        )

        return "✅ Memory stored successfully"


# -------------------------------
# 🔁 Tool Aliases
# -------------------------------


class SearchMemoriesTool(MemorySearchTool):
    name = "search_memories"
    description = "Alias for memory_search"
    args_schema = MemorySearchInput


class MemoryStoreTool(StoreMemoryTool):
    name = "memory_store"
    description = "Alias for store_memory"
    args_schema = StoreMemoryInput
