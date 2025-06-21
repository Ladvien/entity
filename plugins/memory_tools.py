# plugins/memory_tools.py - SYNC VERSION (Event Loop Safe)

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


def run_async_in_thread(coro):
    """Run async code in a separate thread to avoid event loop conflicts"""
    import threading
    import concurrent.futures

    result = None
    exception = None

    def run_in_thread():
        nonlocal result, exception
        try:
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(coro)
            finally:
                loop.close()
        except Exception as e:
            exception = e

    thread = threading.Thread(target=run_in_thread)
    thread.start()
    thread.join()

    if exception:
        raise exception
    return result


class MemorySearchTool(BaseToolPlugin):
    name = "memory_search"
    description = "Search through stored memories for relevant information"
    args_schema = MemorySearchInput

    def _get_memory_system(self):
        """Get memory system with multiple fallback options"""
        # Try direct injection first
        if hasattr(self, "_memory_system"):
            logger.debug("Using directly injected memory system")
            return self._memory_system

        # Try global fallback
        try:
            import src.tools.tools as tools_module

            if hasattr(tools_module, "_global_memory_system"):
                logger.debug("Using global memory system")
                return tools_module._global_memory_system
        except Exception as e:
            logger.debug(f"Could not access global memory system: {e}")

        return None

    async def run(self, input_data: MemorySearchInput) -> str:
        try:
            memory_system = self._get_memory_system()
            if not memory_system:
                logger.error("No memory system available through any method")
                return "[Error] Memory system not available - check tool injection"

            logger.info(f"Searching memories for: {input_data.query}")

            # Use thread-based approach to avoid event loop conflicts
            try:
                memories = run_async_in_thread(
                    memory_system.search_memory(
                        query=input_data.query,
                        thread_id=input_data.thread_id,
                        k=input_data.limit or 5,
                    )
                )
            except Exception as thread_error:
                logger.warning(f"Thread-based search failed: {thread_error}")
                # Final fallback: return a message indicating the search attempted but failed
                return f"[Memory search attempted for '{input_data.query}' but encountered technical difficulties]"

            if not memories:
                return f"No memories found for query: {input_data.query}"

            result_parts = []
            for i, doc in enumerate(memories, 1):
                memory_type = doc.metadata.get("memory_type", "unknown")
                importance = doc.metadata.get("importance_score", 0.5)

                result_parts.append(
                    f"Memory {i} [{memory_type}, importance: {importance:.1f}]: {doc.page_content}"
                )

            logger.info(f"Found {len(memories)} memories for query: {input_data.query}")
            return "\n".join(result_parts)

        except Exception as e:
            logger.exception("MemorySearchTool failed")
            return f"[Error] Memory search failed: {str(e)}"


class StoreMemoryTool(BaseToolPlugin):
    name = "store_memory"
    description = "Store new information in memory for future reference"
    args_schema = StoreMemoryInput

    def _get_memory_system(self):
        """Get memory system with multiple fallback options"""
        # Try direct injection first
        if hasattr(self, "_memory_system"):
            logger.debug("Using directly injected memory system")
            return self._memory_system

        # Try global fallback
        try:
            import src.tools.tools as tools_module

            if hasattr(tools_module, "_global_memory_system"):
                logger.debug("Using global memory system")
                return tools_module._global_memory_system
        except Exception as e:
            logger.debug(f"Could not access global memory system: {e}")

        return None

    async def run(self, input_data: StoreMemoryInput) -> str:
        try:
            memory_system = self._get_memory_system()
            if not memory_system:
                logger.error("No memory system available through any method")
                return "[Error] Memory system not available - check tool injection"

            logger.info(f"Storing memory: {input_data.content[:50]}...")

            # Use thread-based approach to avoid event loop conflicts
            try:
                run_async_in_thread(
                    memory_system.add_memory(
                        thread_id=input_data.thread_id or "default",
                        content=input_data.content,
                        memory_type=input_data.memory_type or "observation",
                        importance_score=input_data.importance_score or 0.5,
                    )
                )
            except Exception as thread_error:
                logger.warning(f"Thread-based storage failed: {thread_error}")
                # Final fallback: return a message indicating the storage attempted but failed
                return f"[Memory storage attempted for '{input_data.content[:50]}...' but encountered technical difficulties]"

            logger.info("Memory stored successfully")
            return f"Memory stored successfully: {input_data.content[:100]}{'...' if len(input_data.content) > 100 else ''}"

        except Exception as e:
            logger.exception("StoreMemoryTool failed")
            return f"[Error] Failed to store memory: {str(e)}"
