# Replace your plugins/memory_tools.py with this version
# This disables memory search temporarily but keeps memory storage working

from typing import Optional
from pydantic import BaseModel, Field
from src.tools.tools import BaseToolPlugin
import logging
import asyncio

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


def get_memory_system():
    """Get memory system with multiple fallback strategies"""

    # Strategy 1: Global fallback - most reliable
    try:
        import src.tools.tools as tools_module

        if (
            hasattr(tools_module, "_global_memory_system")
            and tools_module._global_memory_system is not None
        ):
            logger.debug("✅ Using global memory system")
            return tools_module._global_memory_system
    except Exception as e:
        logger.debug(f"Global memory system not available: {e}")

    # Strategy 2: Try to get from app state (if running in FastAPI context)
    try:
        from src.service.app import app

        if hasattr(app, "state") and hasattr(app.state, "memory_system"):
            logger.debug("✅ Using app state memory system")
            return app.state.memory_system
    except Exception as e:
        logger.debug(f"App state memory system not available: {e}")

    logger.error("❌ No memory system available through any method")
    return None


class MemorySearchTool(BaseToolPlugin):
    name = "memory_search"
    description = "Search through stored memories for relevant information. Use this to find past conversations, user preferences, or relevant context."
    args_schema = MemorySearchInput

    async def run(self, input_data: MemorySearchInput) -> str:
        # TEMPORARY: Return a simple message instead of trying to search
        # This avoids the async event loop issues
        logger.info(
            f"🔍 Memory search requested for: '{input_data.query}' (temporarily disabled)"
        )
        return "Memory search is temporarily unavailable due to technical difficulties. However, I can still store new memories for future use."


class StoreMemoryTool(BaseToolPlugin):
    name = "store_memory"
    description = "Store new information in memory for future reference. Use this to remember important user information, preferences, or context."
    args_schema = StoreMemoryInput

    async def run(self, input_data: StoreMemoryInput) -> str:
        try:
            # First check if we have direct injection (preferred method)
            memory_system = None
            if hasattr(self, "_memory_system") and self._memory_system is not None:
                memory_system = self._memory_system
                logger.debug("✅ Using directly injected memory system")
            else:
                memory_system = get_memory_system()

            if not memory_system:
                error_msg = "Memory system not available. Please ensure the agent is properly initialized."
                logger.error(error_msg)
                return f"[Error] {error_msg}"

            logger.info(
                f"💾 Storing memory: '{input_data.content[:50]}...' in thread '{input_data.thread_id}'"
            )

            # Execute the storage with proper error handling
            try:
                await memory_system.add_memory(
                    thread_id=input_data.thread_id or "default",
                    content=input_data.content,
                    memory_type=input_data.memory_type or "observation",
                    importance_score=input_data.importance_score or 0.5,
                )
            except Exception as store_error:
                logger.warning(f"Memory storage failed: {store_error}")
                return f"[Error] Memory storage failed: {str(store_error)}"

            result = f"✅ Memory stored successfully: '{input_data.content[:100]}{'...' if len(input_data.content) > 100 else ''}'"
            logger.info(result)
            return result

        except Exception as e:
            error_msg = f"Failed to store memory: {str(e)}"
            logger.exception(f"❌ StoreMemoryTool error: {error_msg}")
            return f"[Error] {error_msg}"


# Keep the alias tools but they'll also be temporarily disabled
class SearchMemoriesTool(MemorySearchTool):
    """Alias for memory_search to handle LLM naming inconsistencies"""

    name = "search_memories"
    description = "Search through stored memories for relevant information (alias for memory_search) - temporarily disabled"


class MemoryStoreTool(StoreMemoryTool):
    """Alternative name for store_memory"""

    name = "memory_store"
    description = (
        "Store new information in memory for future reference (alias for store_memory)"
    )
