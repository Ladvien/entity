# src/api/routes.py
"""
FastAPI routes with clean separation of concerns.
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any, Optional, List, Dict
from datetime import datetime
import logging

from src.application_layer import ApplicationService, EntityAgentError


logger = logging.getLogger(__name__)


# Pydantic models for API
class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = "default"


class ChatResponse(BaseModel):
    response: str
    thread_id: str
    has_memory: bool
    memory_stats: Optional[Dict] = None


class HistoryResponse(BaseModel):
    thread_id: str
    conversations: List[str]
    has_memory: bool


class StatusResponse(BaseModel):
    status: str
    entity_name: str
    entity_id: str
    memory_enabled: bool
    timestamp: str
    config_loaded: bool
    services: Dict[str, str]


class APIRoutes:
    """
    API routes class that encapsulates all FastAPI endpoints.
    Uses dependency injection for better testability.
    """

    def __init__(self, app_service: ApplicationService):
        self.app_service = app_service

    def register_routes(self, app: FastAPI) -> None:
        """Register all routes with the FastAPI app."""

        @app.post("/chat", response_model=ChatResponse)
        async def chat(request: ChatRequest):
            """Chat with the entity"""
            try:
                if not self.app_service.is_initialized:
                    raise HTTPException(
                        status_code=500, detail="Entity agent not initialized"
                    )

                response = await self.app_service.process_chat(
                    request.message, request.thread_id
                )

                return ChatResponse(
                    response=response,
                    thread_id=request.thread_id,
                    has_memory=self.app_service.has_memory(),
                    memory_stats=None,
                )
            except EntityAgentError as e:
                logger.error(f"Entity agent error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
            except Exception as e:
                logger.error(f"Unexpected chat error: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @app.get("/history/{thread_id}", response_model=HistoryResponse)
        async def get_history(
            thread_id: str,
            limit: int = Query(default=10, ge=1, le=100),
        ):
            """Get conversation history for a thread"""
            try:
                if not self.app_service.is_initialized:
                    raise HTTPException(
                        status_code=500, detail="Entity agent not initialized"
                    )

                conversations = await self.app_service.get_conversation_history(
                    thread_id, limit
                )

                return HistoryResponse(
                    thread_id=thread_id,
                    conversations=conversations,
                    has_memory=self.app_service.has_memory(),
                )
            except EntityAgentError as e:
                logger.error(f"Entity agent error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
            except Exception as e:
                logger.error(f"History error: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @app.delete("/history/{thread_id}")
        async def delete_history(thread_id: str):
            """Delete conversation history for a thread"""
            try:
                if not self.app_service.is_initialized:
                    raise HTTPException(
                        status_code=500, detail="Entity agent not initialized"
                    )

                success = await self.app_service.delete_conversation(thread_id)

                if success:
                    return {
                        "message": f"Conversation history for thread {thread_id} deleted"
                    }
                else:
                    raise HTTPException(
                        status_code=500, detail="Failed to delete conversation history"
                    )
            except EntityAgentError as e:
                logger.error(f"Entity agent error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
            except Exception as e:
                logger.error(f"Delete error: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @app.post("/reload")
        async def reload_config():
            """Reload configuration"""
            try:
                # This would need to be implemented to reload from file
                # For now, just return success
                return {"message": "Configuration reload not implemented yet"}
            except Exception as e:
                logger.error(f"Reload error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @app.get("/config")
        async def get_config():
            """Get full configuration"""
            try:
                return JSONResponse(
                    content=self.app_service.config.model_dump(
                        by_alias=True, exclude_none=True
                    )
                )
            except Exception as e:
                logger.error(f"Config error: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @app.get("/health", response_model=StatusResponse)
        async def health_check():
            """Health check endpoint"""
            try:
                status = self.app_service.get_status()
                return StatusResponse(
                    status="healthy" if status["initialized"] else "starting",
                    entity_name=status["entity_name"],
                    entity_id=status["entity_id"],
                    memory_enabled=status["has_memory"],
                    timestamp=datetime.now().isoformat(),
                    config_loaded=True,
                    services={
                        "ollama": self.app_service.config.ollama.base_url,
                        "database": f"{self.app_service.config.database.host}:{self.app_service.config.database.port}",
                    },
                )
            except Exception as e:
                logger.error(f"Health check error: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @app.get("/")
        async def root():
            """Root endpoint with system information"""
            try:
                status = self.app_service.get_status()
                return {
                    "message": "Entity Agentic System v2.0",
                    "entity_id": status["entity_id"],
                    "entity_name": status["entity_name"],
                    "memory_enabled": status["has_memory"],
                    "memory_type": (
                        "Vector Memory + PostgreSQL" if status["has_memory"] else "None"
                    ),
                    "status": "ready" if status["initialized"] else "initializing",
                    "config": {
                        "ollama_model": status["ollama_model"],
                        "database_host": status["database_host"],
                        "debug_mode": status["debug_mode"],
                    },
                }
            except Exception as e:
                logger.error(f"Root endpoint error: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")
