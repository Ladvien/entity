from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime

from src.memory.memory_system import MemorySystem
from src.service.agent import EntityAgent
from src.shared.models import (
    ChatRequest,
    ChatResponse,
    ToolExecutionRequest,
    ToolExecutionResponse,
)
from src.core.registry import ServiceRegistry
from src.shared.utils import agent_result_to_response
from src.tools.tools import ToolManager


class EntityRouterFactory:
    def __init__(
        self,
        agent: EntityAgent,
        tool_registry: ToolManager,
        memory_system: MemorySystem,
    ):
        self.agent = agent
        self.tool_registry = tool_registry
        self.memory_system = memory_system

    def get_router(self) -> APIRouter:
        router = APIRouter()

        @router.post("/chat", response_model=ChatResponse, tags=["chat"])
        async def chat(request: ChatRequest):
            try:
                interaction = await self.agent.chat(
                    message=request.message,
                    thread_id=request.thread_id,
                    use_tools=request.use_tools,
                )
                return agent_result_to_response(interaction)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @router.get("/history/{thread_id}", tags=["chat"])
        async def get_history(
            thread_id: str, limit: Optional[int] = Query(default=100, ge=1, le=1000)
        ):
            try:
                interactions = await self.memory_system.get_history(thread_id, limit)
                return {
                    "thread_id": thread_id,
                    "history": [
                        {
                            "user_input": i.raw_input,
                            "agent_output": i.response,
                            "timestamp": i.timestamp.isoformat(),
                            "metadata": {
                                "tools_used": i.tools_used,
                                "use_tools": i.use_tools,
                                "error": i.error,
                                "response_time_ms": i.response_time_ms,
                                "personality_applied": i.agent_personality_applied,
                                "conversation_turn": i.conversation_turn,
                            },
                        }
                        for i in interactions
                    ],
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @router.get("/memory/stats", tags=["memory"])
        async def memory_stats():
            try:
                return await self.memory_system.get_memory_stats()
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @router.get("/memory/search", tags=["memory"])
        async def memory_search(query: str, thread_id: Optional[str] = None):
            try:
                results = await self.memory_system.search_memory(query, thread_id)
                return [doc.page_content for doc in results]
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @router.get("/memory/deep_search", tags=["memory"])
        async def memory_deep_search(query: str, thread_id: Optional[str] = None):
            try:
                results = await self.memory_system.deep_search_memory(query, thread_id)
                return [
                    {
                        "raw_input": i.raw_input,
                        "response": i.response,
                        "timestamp": i.timestamp.isoformat(),
                        "thread_id": i.thread_id,
                    }
                    for i in results
                ]
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @router.get("/tools", tags=["tools"])
        async def list_tools():
            try:
                return {"tools": self.tool_registry.list_tool_names()}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @router.post(
            "/tools/{tool_name}/execute",
            response_model=ToolExecutionResponse,
            tags=["tools"],
        )
        async def execute_tool(tool_name: str, request: ToolExecutionRequest):
            try:
                tool = self.tool_registry.get_tool(tool_name)
                if not tool:
                    raise HTTPException(
                        status_code=404, detail=f"Tool '{tool_name}' not found"
                    )

                start_time = datetime.utcnow()
                result = await tool.afunc(**request.parameters)
                execution_time = (datetime.utcnow() - start_time).total_seconds()

                return ToolExecutionResponse(
                    result=result, execution_time=execution_time, success=True
                )
            except HTTPException:
                raise
            except Exception as e:
                return ToolExecutionResponse(
                    result=None, execution_time=0.0, success=False, error=str(e)
                )

        @router.get("/health", tags=["system"])
        async def health_check():
            services = ServiceRegistry.list_services()
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "2.0.0",
                "architecture": "ServiceRegistry",
                "services": services,
                "registry_initialized": ServiceRegistry.is_initialized(),
                "service_count": len(services),
                "features": {
                    "postgresql": ServiceRegistry.has("db_connection"),
                    "tools": ServiceRegistry.has("tool_manager"),
                    "adapters": ServiceRegistry.has("output_adapter_manager"),
                    "chat_interactions": True,
                    "service_registry": True,
                },
            }

        @router.get("/debug/services", tags=["system"])
        async def list_services():
            if not ServiceRegistry.is_initialized():
                raise HTTPException(
                    status_code=503, detail="ServiceRegistry not initialized"
                )
            services = ServiceRegistry.list_services()
            return {
                "services": services,
                "initialized": ServiceRegistry.is_initialized(),
                "service_count": len(services),
                "available_services": list(services.keys()),
            }

        return router
