# entity_client/client.py
"""
Enhanced REST API client with memory endpoints
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx

from shared.models import ChatRequest, ChatResponse, MemoryStatsResponse

logger = logging.getLogger(__name__)


class EntityAPIClient:
    """REST API client for Entity Agent Service with memory support"""

    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = httpx.AsyncClient(timeout=timeout)

    async def chat(
        self,
        message: str,
        thread_id: str = "default",
        use_tools: bool = True,
        use_memory: bool = True,
    ) -> ChatResponse:
        """Send a chat message to the entity agent"""
        try:
            response = await self.session.post(
                f"{self.base_url}/api/v1/chat",
                json={
                    "message": message,
                    "thread_id": thread_id,
                    "use_tools": use_tools,
                    "use_memory": use_memory,
                },
            )
            response.raise_for_status()
            return ChatResponse(**response.json())

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            raise
        except Exception as e:
            logger.error(f"Chat request failed: {e}")
            raise

    async def get_history(
        self, thread_id: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get chat history for a thread"""
        try:
            params = {}
            if limit:
                params["limit"] = limit

            response = await self.session.get(
                f"{self.base_url}/api/v1/history/{thread_id}", params=params
            )
            response.raise_for_status()
            data = response.json()
            return data.get("history", [])

        except Exception as e:
            logger.error(f"Failed to get history: {e}")
            return []

    async def search_memory(
        self, query: str, thread_id: Optional[str] = None, limit: int = 5
    ) -> Dict[str, Any]:
        """Search vector memory"""
        try:
            params = {"query": query, "limit": limit}
            if thread_id:
                params["thread_id"] = thread_id

            response = await self.session.get(
                f"{self.base_url}/api/v1/memory/search", params=params
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            return {"memories": []}

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        try:
            response = await self.session.get(f"{self.base_url}/api/v1/memory/stats")
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {}

    async def list_tools(self) -> List[str]:
        """List available tools"""
        try:
            response = await self.session.get(f"{self.base_url}/api/v1/tools")
            response.raise_for_status()
            data = response.json()
            return data.get("tools", [])

        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return []

    async def execute_tool(
        self, tool_name: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a specific tool"""
        try:
            response = await self.session.post(
                f"{self.base_url}/api/v1/tools/{tool_name}/execute",
                json={"tool_name": tool_name, "parameters": parameters},
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            raise

    async def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        try:
            response = await self.session.get(f"{self.base_url}/api/v1/health")
            response.raise_for_status()
            return response.json()

        except Exception:
            return {"status": "unhealthy", "error": "Connection failed"}

    async def close(self):
        """Close the client session"""
        await self.session.aclose()
