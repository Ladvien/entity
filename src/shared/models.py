# src/shared/models.py (update the existing file)

from dataclasses import dataclass
import uuid
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from src.shared.agent_result import AgentResult


class ChatInteraction(BaseModel):
    """Standardized chat interaction model for storage and retrieval"""

    # Core interaction data
    interaction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    thread_id: str = Field(..., description="Conversation thread identifier")
    timestamp: datetime = Field(..., description="When the interaction occurred")

    # Input/Output tracking
    raw_input: str = Field(..., description="User's original input")
    response: str = Field(..., description="The agent's response")
    raw_output: str = Field(..., description="Agent's raw output before processing")

    # Tool and memory usage
    tools_used: List[str] = Field(
        default_factory=list, description="Tools used in this interaction"
    )
    memory_context_used: bool = Field(
        default=False, description="Whether memory context was used"
    )
    memory_context: str = Field(
        default="", description="Actual memory context provided"
    )

    # Behavior toggles
    use_tools: bool = Field(default=True, description="Whether tools were enabled")
    use_memory: bool = Field(default=True, description="Whether memory was enabled")

    # Metadata and tracking
    error: Optional[str] = Field(
        default=None, description="Error message if interaction failed"
    )
    response_time_ms: Optional[float] = Field(
        default=None, description="How long it took to generate the response"
    )
    token_count: Optional[int] = Field(
        default=None, description="Total number of tokens used"
    )
    conversation_turn: Optional[int] = Field(
        default=None, description="Which turn in the conversation this is"
    )
    user_id: Optional[str] = Field(
        default=None, description="User associated with this interaction"
    )

    # Personality application
    agent_personality_applied: bool = Field(
        default=False, description="If a personality prompt was applied"
    )
    personality_adjustments: List[str] = Field(
        default_factory=list, description="Adjustments applied to personality"
    )

    # Extended metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Extra metadata for future use"
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
                "memory_context": self.memory_context,
                "use_tools": self.use_tools,
                "use_memory": self.use_memory,
                "error": self.error,
                "response_time_ms": self.response_time_ms,
                "token_count": self.token_count,
                "conversation_turn": self.conversation_turn,
                "user_id": self.user_id,
                "agent_personality_applied": self.agent_personality_applied,
                "personality_adjustments": self.personality_adjustments,
                "metadata": self.metadata,
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
            memory_context=metadata.get("memory_context", ""),
            use_tools=metadata.get("use_tools", True),
            use_memory=metadata.get("use_memory", True),
            error=metadata.get("error"),
            response_time_ms=metadata.get("response_time_ms"),
            token_count=metadata.get("token_count"),
            conversation_turn=metadata.get("conversation_turn"),
            user_id=metadata.get("user_id"),
            agent_personality_applied=metadata.get("agent_personality_applied", False),
            personality_adjustments=metadata.get("personality_adjustments", []),
            metadata=metadata.get("metadata", {}),
        )

    def add_personality_adjustment(self, note: str):
        """Record a personality-based modification applied during generation"""
        self.agent_personality_applied = True
        self.personality_adjustments.append(note)

    def add_performance_metrics(self, token_count: int, latency_ms: float):
        """Attach performance metrics to this interaction"""
        self.token_count = token_count
        self.response_time_ms = latency_ms


# Keep existing models as well
class ChatRequest(BaseModel):
    """Chat request model"""

    message: str
    thread_id: str = "default"
    use_tools: bool = True
    use_memory: bool = True


class ChatResponse(BaseModel):
    thread_id: str
    timestamp: datetime
    raw_input: str
    raw_output: str
    response: str
    tools_used: Optional[List[str]] = []
    token_count: Optional[int] = 0
    memory_context: Optional[str] = ""
    intermediate_steps: Optional[List[dict]] = []

    @classmethod
    def from_result(cls, interaction: AgentResult) -> "ChatResponse":
        return cls(
            thread_id=interaction.thread_id,
            timestamp=interaction.timestamp,
            raw_input=interaction.raw_input,
            raw_output=interaction.raw_output,
            response=interaction.final_response,
            tools_used=interaction.tools_used,
            token_count=interaction.token_count,
            memory_context=interaction.memory_context,
            intermediate_steps=interaction.intermediate_steps,
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


class ConversationSummary(BaseModel):
    """
    Helper dataclass for conversation-level statistics and summaries.
    """

    thread_id: str
    total_interactions: int
    start_time: datetime
    last_interaction: datetime
    total_tools_used: int
    memory_usage_percentage: float
    common_topics: List[str] = Field(default_factory=list)
    error_count: int = 0
    average_response_time_ms: Optional[float] = None

    @classmethod
    def from_interactions(
        cls, interactions: List[ChatInteraction]
    ) -> "ConversationSummary":
        """Create summary from a list of interactions"""
        if not interactions:
            raise ValueError("Cannot create summary from empty interaction list")

        thread_id = interactions[0].thread_id
        total_interactions = len(interactions)

        # Sort by timestamp to get start/end times
        sorted_interactions = sorted(interactions, key=lambda x: x.timestamp)
        start_time = sorted_interactions[0].timestamp
        last_interaction = sorted_interactions[-1].timestamp

        # Calculate statistics
        total_tools_used = sum(len(i.tools_used) for i in interactions)
        memory_used_count = sum(1 for i in interactions if i.memory_context_used)
        memory_usage_percentage = (memory_used_count / total_interactions) * 100

        error_count = sum(1 for i in interactions if i.error)

        # Calculate average response time
        response_times = [
            i.response_time_ms for i in interactions if i.response_time_ms is not None
        ]
        average_response_time_ms = (
            sum(response_times) / len(response_times) if response_times else None
        )

        return cls(
            thread_id=thread_id,
            total_interactions=total_interactions,
            start_time=start_time,
            last_interaction=last_interaction,
            total_tools_used=total_tools_used,
            memory_usage_percentage=memory_usage_percentage,
            error_count=error_count,
            average_response_time_ms=average_response_time_ms,
        )
