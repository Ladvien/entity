# plugins/memory_tools.py - FIXED VERSION
from typing import Optional
from pydantic import BaseModel, Field
from src.tools.tools import BaseToolPlugin
from src.core.registry import (
    ServiceRegistry,
)  # Use ServiceRegistry directly for better error handling
import logging

logger = logging.getLogger(__name__)


class MemorySearchInput(BaseModel):
    query: str = Field(..., description="Search query for memories")
    thread_id: Optional[str] = Field(
        default="default", description="Thread ID to search within"
    )
    limit: Optional[int] = Field(
        default=5, description="Maximum number of memories to return"
    )


class StoreMemoryInput(BaseModel):
    content: str = Field(..., description="Memory content to store")
    thread_id: Optional[str] = Field(
        default="default", description="Thread ID to associate with"
    )
    memory_type: Optional[str] = Field(
        default="observation", description="Type of memory"
    )
    importance_score: Optional[float] = Field(
        default=0.5, description="Importance score (0-1)"
    )


class MemorySearchTool(BaseToolPlugin):
    name = "memory_search"
    description = "Search through stored memories for relevant information. Use this to find past conversations, user preferences, or relevant context."
    args_schema = MemorySearchInput

    async def run(self, input_data: MemorySearchInput) -> str:
        try:
            # Use ServiceRegistry directly with default parameter for graceful handling
            memory_system = ServiceRegistry.try_get("memory_system")
            if not memory_system:
                return "Memory system not available. Please ensure the agent is properly initialized."

            logger.info(
                f"🔍 Searching memories for: '{input_data.query}' in thread '{input_data.thread_id}'"
            )

            # Search memories using the clean interface
            memories = await memory_system.search_memory(
                query=input_data.query,
                thread_id=input_data.thread_id,
                k=input_data.limit,
            )

            if not memories:
                return f"No memories found for query: '{input_data.query}'"

            # Format results
            results = []
            for i, memory in enumerate(memories, 1):
                content = memory.page_content
                metadata = memory.metadata
                memory_type = metadata.get("memory_type", "unknown")
                importance = metadata.get("importance_score", 0.0)

                results.append(
                    f"{i}. [{memory_type}] {content} (importance: {importance:.1f})"
                )

            result_text = f"Found {len(memories)} memories:\n" + "\n".join(results)
            logger.info(f"✅ Memory search completed: {len(memories)} results")
            return result_text

        except Exception as e:
            logger.exception("MemorySearchTool failed")
            return f"[Error] Memory search failed: {str(e)}"


class StoreMemoryTool(BaseToolPlugin):
    name = "store_memory"
    description = "Store new information in memory for future reference. Use this to remember important user information, preferences, or context."
    args_schema = StoreMemoryInput

    async def run(self, input_data: StoreMemoryInput) -> str:
        try:
            # Use ServiceRegistry directly with default parameter for graceful handling
            memory_system = ServiceRegistry.try_get("memory_system")
            if not memory_system:
                return "Memory system not available. Please ensure the agent is properly initialized."

            if not memory_system:
                return "Memory system not available. Please ensure the agent is properly initialized."

            logger.info(
                f"💾 Storing memory: '{input_data.content[:50]}...' in thread '{input_data.thread_id}'"
            )

            # Store the memory using the clean interface
            await memory_system.add_memory(
                thread_id=input_data.thread_id or "default",
                content=input_data.content,
                memory_type=input_data.memory_type or "observation",
                importance_score=input_data.importance_score or 0.5,
            )

            result = f"✅ Memory stored successfully: '{input_data.content[:100]}{'...' if len(input_data.content) > 100 else ''}'"
            logger.info(result)
            return result

        except Exception as e:
            error_msg = f"Failed to store memory: {str(e)}"
            logger.exception(f"❌ StoreMemoryTool error: {error_msg}")
            return f"[Error] {error_msg}"


# Keep the alias tools for backward compatibility
class SearchMemoriesTool(MemorySearchTool):
    """Alias for memory_search to handle LLM naming inconsistencies"""

    name = "search_memories"
    description = "Search through stored memories for relevant information (alias for memory_search)"


class MemoryStoreTool(StoreMemoryTool):
    """Alternative name for store_memory"""

    name = "memory_store"
    description = (
        "Store new information in memory for future reference (alias for store_memory)"
    )
