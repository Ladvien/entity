# src/service/routes.py - Add ServiceRegistry support to health check

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime

from src.shared.models import (
    ChatRequest,
    ChatResponse,
    ChatInteraction,
    ToolExecutionRequest,
    ToolExecutionResponse,
    MemoryStatsResponse,
)
from src.core.registry import ServiceRegistry  # NEW IMPORT


class EntityRouterFactory:
    def __init__(self, agent, memory_system, tool_registry, storage):
        self.agent = agent
        self.memory_system = memory_system
        self.tool_registry = tool_registry
        self.storage = storage

    def get_router(self) -> APIRouter:
        router = APIRouter()

        @router.post("/chat", response_model=ChatResponse)
        async def chat(request: ChatRequest):
            try:
                # Get ChatInteraction from agent (using new method)
                interaction = await self.agent.chat(
                    message=request.message,
                    thread_id=request.thread_id,
                    use_tools=request.use_tools,
                    use_memory=request.use_memory,
                )

                # Convert ChatInteraction to ChatResponse for API response
                response = ChatResponse.from_interaction(interaction)
                return response

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @router.get("/history/{thread_id}")
        async def get_history(
            thread_id: str, limit: Optional[int] = Query(default=100, ge=1, le=1000)
        ):
            try:
                # Get ChatInteraction objects from storage
                interactions = await self.storage.get_history(thread_id, limit)

                # Convert ChatInteraction objects to dict format for API response
                history = []
                for interaction in interactions:
                    history.append(
                        {
                            "user_input": interaction.raw_input,
                            "agent_output": interaction.response,
                            "timestamp": interaction.timestamp.isoformat(),
                            "metadata": {
                                "tools_used": interaction.tools_used,
                                "memory_context_used": interaction.memory_context_used,
                                "use_tools": interaction.use_tools,
                                "use_memory": interaction.use_memory,
                                "error": interaction.error,
                                "response_time_ms": interaction.response_time_ms,
                                "personality_applied": interaction.agent_personality_applied,
                                "conversation_turn": interaction.conversation_turn,
                            },
                        }
                    )

                return {"thread_id": thread_id, "history": history}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @router.get("/memory/search")
        async def search_memory(
            query: str,
            thread_id: Optional[str] = Query(default=None),
            limit: int = Query(default=5, ge=1, le=20),
        ):
            try:
                memories = await self.memory_system.search_memory(
                    query, thread_id, k=limit
                )
                return {
                    "query": query,
                    "thread_id": thread_id,
                    "memories": [
                        {"content": doc.page_content, "metadata": doc.metadata}
                        for doc in memories
                    ],
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @router.get("/memory/stats", response_model=MemoryStatsResponse)
        async def get_memory_stats():
            try:
                stats = await self.agent.get_memory_stats()
                return MemoryStatsResponse(**stats)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @router.get("/tools")
        async def list_tools():
            try:
                return {"tools": self.tool_registry.list_tool_names()}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @router.post("/tools/{tool_name}/execute", response_model=ToolExecutionResponse)
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

        @router.get("/health")
        async def health_check():
            """Enhanced health check using ServiceRegistry"""
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
                    "vector_memory": ServiceRegistry.has("memory_system"),
                    "postgresql": ServiceRegistry.has("db_connection"),
                    "tools": ServiceRegistry.has("tool_manager"),
                    "output_adapters": ServiceRegistry.has("output_adapter_manager"),
                    "chat_interactions": True,
                    "service_registry": True,  # New feature!
                },
            }

        @router.get("/debug/services")
        async def list_services():
            """Debug endpoint to see all registered services"""
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

        # New endpoint to get detailed interaction by ID
        @router.get("/interaction/{interaction_id}")
        async def get_interaction(interaction_id: str):
            """Get detailed information about a specific interaction"""
            try:
                # You'd need to implement this in your storage layer
                # interaction = await self.storage.get_interaction_by_id(interaction_id)
                # return interaction.to_api_response() if interaction else None

                # For now, return a placeholder
                return {"error": "Not implemented yet"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        # New endpoint for conversation analytics
        @router.get("/analytics/{thread_id}")
        async def get_conversation_analytics(thread_id: str):
            """Get analytics for a conversation thread"""
            try:
                interactions = await self.storage.get_history(thread_id, limit=1000)

                if not interactions:
                    return {"error": "No interactions found for this thread"}

                # Calculate analytics
                total_interactions = len(interactions)
                total_tools_used = sum(len(i.tools_used) for i in interactions)
                memory_usage_count = sum(
                    1 for i in interactions if i.memory_context_used
                )
                error_count = sum(1 for i in interactions if i.error)

                # Calculate average response time
                response_times = [
                    i.response_time_ms for i in interactions if i.response_time_ms
                ]
                avg_response_time = (
                    sum(response_times) / len(response_times)
                    if response_times
                    else None
                )

                # Get personality application stats
                personality_applications = sum(
                    1 for i in interactions if i.agent_personality_applied
                )

                return {
                    "thread_id": thread_id,
                    "total_interactions": total_interactions,
                    "tools_usage": {
                        "total_tools_used": total_tools_used,
                        "average_per_interaction": (
                            total_tools_used / total_interactions
                            if total_interactions > 0
                            else 0
                        ),
                    },
                    "memory_usage": {
                        "usage_count": memory_usage_count,
                        "usage_percentage": (
                            (memory_usage_count / total_interactions * 100)
                            if total_interactions > 0
                            else 0
                        ),
                    },
                    "performance": {
                        "average_response_time_ms": avg_response_time,
                        "error_count": error_count,
                        "error_rate": (
                            (error_count / total_interactions * 100)
                            if total_interactions > 0
                            else 0
                        ),
                    },
                    "personality": {
                        "applications": personality_applications,
                        "application_rate": (
                            (personality_applications / total_interactions * 100)
                            if total_interactions > 0
                            else 0
                        ),
                    },
                    "timeline": {
                        "first_interaction": (
                            interactions[-1].timestamp.isoformat()
                            if interactions
                            else None
                        ),
                        "last_interaction": (
                            interactions[0].timestamp.isoformat()
                            if interactions
                            else None
                        ),
                    },
                    "architecture": "ServiceRegistry",  # Show we're using new architecture
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        return router
