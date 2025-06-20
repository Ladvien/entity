# src/service/routes.py

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
                # Get ChatInteraction from agent
                interaction = await self.agent.chat(
                    message=request.message,
                    thread_id=request.thread_id,
                    use_tools=request.use_tools,
                    use_memory=request.use_memory,
                )

                # Convert to ChatResponse for API response
                response = ChatResponse.from_interaction(interaction)
                return response

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @router.get("/history/{thread_id}")
        async def get_history(
            thread_id: str, limit: Optional[int] = Query(default=100, ge=1, le=1000)
        ):
            try:
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
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "2.0.0",
                "features": {
                    "vector_memory": True,
                    "postgresql": True,
                    "tools": True,
                },
            }

        return router
