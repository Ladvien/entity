# src/shared/models.py (update the existing file)

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatInteraction(BaseModel):
    """Standardized chat interaction model for storage and retrieval"""

    # Core interaction data
    response: str = Field(..., description="The agent's response")
    thread_id: str = Field(..., description="Conversation thread identifier")
    timestamp: datetime = Field(..., description="When the interaction occurred")

    # Input/Output tracking
    raw_input: str = Field(..., description="User's original input")
    raw_output: str = Field(..., description="Agent's raw output before processing")

    # Tool and memory usage
    tools_used: List[str] = Field(
        default_factory=list, description="Tools used in this interaction"
    )
    memory_context_used: bool = Field(
        default=False, description="Whether memory context was used"
    )

    # Additional metadata
    use_tools: bool = Field(default=True, description="Whether tools were enabled")
    use_memory: bool = Field(default=True, description="Whether memory was enabled")
    error: Optional[str] = Field(
        default=None, description="Error message if interaction failed"
    )

    class Config:
        json_encoders = {datetime: lambda dt: dt.isoformat()}

    def to_storage_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for database storage"""
        return {
            "thread_id": self.thread_id,
            "user_input": self.raw_input,
            "agent_output": self.response,
            "metadata": {
                "timestamp": self.timestamp,
                "tools_used": self.tools_used,
                "raw_output": self.raw_output,
                "memory_context_used": self.memory_context_used,
                "use_tools": self.use_tools,
                "use_memory": self.use_memory,
                "error": self.error,
            },
        }

    @classmethod
    def from_storage_dict(cls, data: Dict[str, Any]) -> "ChatInteraction":
        """Create ChatInteraction from database storage format"""
        metadata = data.get("metadata", {})

        return cls(
            response=data["agent_output"],
            thread_id=data["thread_id"],
            timestamp=metadata.get("timestamp", datetime.utcnow()),
            raw_input=data["user_input"],
            raw_output=metadata.get("raw_output", data["agent_output"]),
            tools_used=metadata.get("tools_used", []),
            memory_context_used=metadata.get("memory_context_used", False),
            use_tools=metadata.get("use_tools", True),
            use_memory=metadata.get("use_memory", True),
            error=metadata.get("error"),
        )


# Keep existing models as well
class ChatRequest(BaseModel):
    """Chat request model"""

    message: str
    thread_id: str = "default"
    use_tools: bool = True
    use_memory: bool = True


class ChatResponse(BaseModel):
    """Chat response model - now based on ChatInteraction"""

    response: str
    thread_id: str
    timestamp: datetime
    tools_used: Optional[List[str]] = None
    raw_input: str
    raw_output: str
    memory_context_used: bool = False
    entity_name: Optional[str] = None

    @classmethod
    def from_interaction(cls, interaction: ChatInteraction) -> "ChatResponse":
        """Create ChatResponse from ChatInteraction"""
        return cls(
            response=interaction.response,
            thread_id=interaction.thread_id,
            timestamp=interaction.timestamp,
            tools_used=interaction.tools_used,
            raw_input=interaction.raw_input,
            raw_output=interaction.raw_output,
            memory_context_used=interaction.memory_context_used,
        )

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
