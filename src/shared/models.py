# shared/models.py
"""
Updated shared models with memory support
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatRequest(BaseModel):
    """Chat request model"""

    message: str
    thread_id: str = "default"
    use_tools: bool = True
    use_memory: bool = True


class ChatResponse(BaseModel):
    """Chat response model"""

    response: str
    thread_id: str
    timestamp: datetime
    tools_used: Optional[List[str]] = None
    raw_input: str
    raw_output: str
    memory_context_used: bool = False
    entity_name: Optional[str] = None  # ← Add this

    class Config:
        extra = "allow"


class MemoryStatsResponse(BaseModel):
    """Memory statistics response"""

    total_memories: int
    total_conversations: int
    memory_types: Dict[str, int]
    emotions: Dict[str, int]
    top_topics: Dict[str, int]
    backend: str
    vector_dimensions: Optional[int] = None
    embedding_model: Optional[str] = None


class ToolExecutionRequest(BaseModel):
    """Tool execution request"""

    tool_name: str
    parameters: Dict[str, Any]


class ToolExecutionResponse(BaseModel):
    """Tool execution response"""

    result: Any
    execution_time: float
    success: bool
    error: Optional[str] = None
