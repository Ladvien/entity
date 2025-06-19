# entity_service/api/routes.py
"""
FastAPI routes with memory endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime

from shared.models import (
    ChatRequest,
    ChatResponse,
    ToolExecutionRequest,
    ToolExecutionResponse,
    MemoryStatsResponse,
)

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat with the entity agent"""
    try:
        agent = router.app.state.agent
        result = await agent.chat(
            message=request.message,
            thread_id=request.thread_id,
            use_tools=request.use_tools,
            use_memory=request.use_memory,
        )

        return ChatResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{thread_id}")
async def get_history(
    thread_id: str, limit: Optional[int] = Query(default=100, ge=1, le=1000)
):
    """Get raw chat history for a thread"""
    try:
        storage = router.app.state.storage
        history = await storage.get_history(thread_id, limit)
        return {"thread_id": thread_id, "history": history}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/search")
async def search_memory(
    query: str,
    thread_id: Optional[str] = Query(default=None),
    limit: int = Query(default=5, ge=1, le=20),
):
    """Search vector memory"""
    try:
        memory_system = router.app.state.memory_system
        memories = await memory_system.search_memory(query, thread_id, k=limit)

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
    """Get memory system statistics"""
    try:
        agent = router.app.state.agent
        stats = await agent.get_memory_stats()
        return MemoryStatsResponse(**stats)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools")
async def list_tools():
    """List available tools"""
    try:
        tool_registry = router.app.state.tool_registry
        return {"tools": tool_registry.list_tool_names()}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tools/{tool_name}/execute", response_model=ToolExecutionResponse)
async def execute_tool(tool_name: str, request: ToolExecutionRequest):
    """Execute a specific tool"""
    try:
        tool_registry = router.app.state.tool_registry
        tool = tool_registry.get_tool(tool_name)

        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

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
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "features": {"vector_memory": True, "postgresql": True, "tools": True},
    }


def create_routes() -> APIRouter:
    """Create and return the router"""
    return router
