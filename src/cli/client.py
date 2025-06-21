import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx

from src.shared.models import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)


class EntityAPIClient:
    """REST API client for Entity Agent Service (memory removed)"""

    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = httpx.AsyncClient(timeout=timeout)

    async def send_message(self, message: str) -> ChatResponse:
        """Alias for chat(), used by CLI"""
        return await self.chat(message)

    async def chat(
        self,
        message: str,
        thread_id: str = "default",
        use_tools: bool = True,
    ) -> ChatResponse:
        """Send a chat message to the entity agent"""
        try:
            response = await self.session.post(
                f"{self.base_url}/api/v1/chat",
                json={
                    "message": message,
                    "thread_id": thread_id,
                    "use_tools": use_tools,
                },
                timeout=60.0,
            )
            response.raise_for_status()

            return ChatResponse(**response.json())

        except httpx.HTTPStatusError as e:
            print(f"DEBUG: HTTP error: {e}, Response: {e.response.text}")
            logger.error(f"HTTP error: {e}")
            raise
        except httpx.TimeoutException as e:
            print(f"DEBUG: Timeout error: {e}")
            logger.error(f"Timeout error: {e}")
            raise
        except Exception as e:
            print(f"DEBUG: Other error: {e}")
            logger.error(f"Chat request failed: {e}")
            raise

    async def get_history(
        self, thread_id: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
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

    async def list_tools(self) -> List[str]:
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
        try:
            response = await self.session.get(f"{self.base_url}/api/v1/health")
            response.raise_for_status()
            return response.json()

        except Exception:
            return {"status": "unhealthy", "error": "Connection failed"}

    async def close(self):
        await self.session.aclose()
