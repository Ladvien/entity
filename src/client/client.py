# src/client/client.py - UPDATED VERSION WITH TTS SUPPORT

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx

from src.shared.agent_result import AgentResult
from src.shared.models import ChatRequest, ChatResponse


logger = logging.getLogger(__name__)


class EntityAPIClient:
    """REST API client for Entity Agent Service with TTS support"""

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
    ) -> AgentResult:
        """Send a chat message to the entity agent with TTS support"""
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
            data = response.json()

            # ✅ Convert ChatResponse to AgentResult with TTS data
            chat_response = ChatResponse(**data)

            # Convert serialized react_steps back to ReActStep objects
            react_steps = []
            if chat_response.react_steps:
                from src.shared.react_step import ReActStep

                for step_data in chat_response.react_steps:
                    react_steps.append(
                        ReActStep(
                            thought=step_data.get("thought", ""),
                            action=step_data.get("action", ""),
                            action_input=step_data.get("action_input", ""),
                            observation=step_data.get("observation", ""),
                            final_answer=step_data.get("final_answer", ""),
                            memory_type=step_data.get("memory_type", "agent_step"),
                        )
                    )

            # Create AgentResult with TTS metadata
            agent_result = AgentResult(
                thread_id=chat_response.thread_id,
                timestamp=chat_response.timestamp,
                raw_input=chat_response.raw_input,
                raw_output=chat_response.raw_output,
                final_response=chat_response.response,
                tools_used=chat_response.tools_used or [],
                token_count=chat_response.token_count or 0,
                memory_context=chat_response.memory_context or "",
                intermediate_steps=chat_response.intermediate_steps or [],
                react_steps=react_steps,
            )

            # 🎵 Add TTS metadata to AgentResult
            if hasattr(chat_response, "tts_enabled") and chat_response.tts_enabled:
                agent_result.tts_enabled = chat_response.tts_enabled
                agent_result.audio_file_id = getattr(
                    chat_response, "audio_file_id", None
                )
                agent_result.audio_duration = getattr(
                    chat_response, "audio_duration", None
                )
                agent_result.tts_voice = getattr(chat_response, "tts_voice", None)
                agent_result.tts_settings = getattr(chat_response, "tts_settings", {})

                # Also add to metadata for compatibility
                if not hasattr(agent_result, "metadata"):
                    agent_result.metadata = {}

                agent_result.metadata.update(
                    {
                        "tts_enabled": chat_response.tts_enabled,
                        "audio_file_id": agent_result.audio_file_id,
                        "audio_duration": agent_result.audio_duration,
                        "tts_voice": agent_result.tts_voice,
                        "tts_settings": agent_result.tts_settings,
                    }
                )

            return agent_result

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}, Response: {e.response.text}")
            raise
        except httpx.TimeoutException as e:
            logger.error(f"Timeout error: {e}")
            raise
        except Exception as e:
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

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory stats from the entity agent"""
        try:
            response = await self.session.get(f"{self.base_url}/api/v1/memory/stats")
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {"status": "error", "message": str(e)}

    async def download_audio(
        self, audio_file_id: str, save_path: str = None
    ) -> Optional[str]:
        """Download audio file from TTS server"""
        try:
            # Try the main server first
            response = await self.session.get(
                f"{self.base_url}/api/v1/audio/{audio_file_id}"
            )

            if response.status_code == 404:
                # Try the TTS server directly (fallback)
                tts_server_url = (
                    "http://192.168.1.110:8888"  # This should come from config
                )
                response = await self.session.get(
                    f"{tts_server_url}/audio/{audio_file_id}"
                )

            response.raise_for_status()

            if save_path is None:
                save_path = f"./downloaded_audio/{audio_file_id}.wav"

            # Ensure directory exists
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)

            with open(save_path, "wb") as f:
                f.write(response.content)

            logger.info(f"📥 Downloaded audio: {save_path}")
            return save_path

        except Exception as e:
            logger.error(f"Failed to download audio: {e}")
            return None

    async def close(self):
        await self.session.aclose()
