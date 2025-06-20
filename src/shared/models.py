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


from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import json
import uuid


@dataclass
class ChatInteraction:
    """
    Comprehensive dataclass for storing chat interactions between user and AI agent.
    Designed to work seamlessly with PostgreSQL storage and your existing codebase.
    """

    # Core interaction data - required fields
    response: str  # The agent's final response to the user
    thread_id: str  # Conversation thread identifier
    raw_input: str  # User's original input message

    # Timestamp - auto-generated if not provided
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Processing data
    raw_output: str = ""  # Agent's raw output before personality adjustments

    # Tool and memory usage tracking
    tools_used: List[str] = field(default_factory=list)
    memory_context_used: bool = False
    memory_context: str = ""  # The actual memory context that was used

    # Configuration flags
    use_tools: bool = True
    use_memory: bool = True

    # Error handling
    error: Optional[str] = None

    # Performance metrics
    response_time_ms: Optional[float] = None
    token_count: Optional[int] = None

    # Conversation metadata
    conversation_turn: Optional[int] = None  # Turn number in conversation
    user_id: Optional[str] = None  # If you need user tracking

    # Agent state information
    agent_personality_applied: bool = False
    personality_adjustments: List[str] = field(default_factory=list)

    # Advanced metadata for extensibility
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Unique identifier for this interaction
    interaction_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        """Post-initialization processing"""
        # Ensure raw_output defaults to response if not set
        if not self.raw_output:
            self.raw_output = self.response

        # Validate required fields
        if not self.raw_input.strip():
            raise ValueError("raw_input cannot be empty")
        if not self.response.strip():
            raise ValueError("response cannot be empty")
        if not self.thread_id.strip():
            raise ValueError("thread_id cannot be empty")

    @classmethod
    def create_from_agent_response(
        cls,
        user_message: str,
        agent_response: Dict[str, Any],
        thread_id: str = "default",
    ) -> "ChatInteraction":
        """
        Factory method to create ChatInteraction from your agent's response format.

        Args:
            user_message: The user's input message
            agent_response: Dictionary returned by your EntityAgent.chat() method
            thread_id: Conversation thread ID
        """
        return cls(
            response=agent_response.get("response", ""),
            thread_id=thread_id,
            raw_input=user_message,
            timestamp=agent_response.get("timestamp", datetime.utcnow()),
            raw_output=agent_response.get(
                "raw_output", agent_response.get("response", "")
            ),
            tools_used=agent_response.get("tools_used", []),
            memory_context_used=agent_response.get("memory_context_used", False),
            error=agent_response.get("error"),
            metadata=agent_response.get("metadata", {}),
        )

    def to_storage_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary format optimized for database storage.
        Matches your PostgreSQL schema structure.
        """
        return {
            "thread_id": self.thread_id,
            "timestamp": self.timestamp,
            "response": self.response,
            "raw_input": self.raw_input,
            "raw_output": self.raw_output,
            "tools_used": json.dumps(self.tools_used),
            "memory_context_used": self.memory_context_used,
            "use_tools": self.use_tools,
            "use_memory": self.use_memory,
            "error_message": self.error,
            "metadata": json.dumps(
                {
                    "interaction_id": self.interaction_id,
                    "memory_context": self.memory_context,
                    "response_time_ms": self.response_time_ms,
                    "token_count": self.token_count,
                    "conversation_turn": self.conversation_turn,
                    "user_id": self.user_id,
                    "agent_personality_applied": self.agent_personality_applied,
                    "personality_adjustments": self.personality_adjustments,
                    **self.metadata,
                }
            ),
        }

    @classmethod
    def from_storage_dict(cls, data: Dict[str, Any]) -> "ChatInteraction":
        """
        Create ChatInteraction from database storage format.
        Handles JSON deserialization and metadata extraction.
        """
        # Parse JSON fields safely
        tools_used = []
        if data.get("tools_used"):
            try:
                tools_used = json.loads(data["tools_used"])
            except (json.JSONDecodeError, TypeError):
                tools_used = []

        metadata = {}
        if data.get("metadata"):
            try:
                metadata = json.loads(data["metadata"])
            except (json.JSONDecodeError, TypeError):
                metadata = {}

        # Extract metadata fields
        interaction_id = metadata.pop("interaction_id", str(uuid.uuid4()))
        memory_context = metadata.pop("memory_context", "")
        response_time_ms = metadata.pop("response_time_ms", None)
        token_count = metadata.pop("token_count", None)
        conversation_turn = metadata.pop("conversation_turn", None)
        user_id = metadata.pop("user_id", None)
        agent_personality_applied = metadata.pop("agent_personality_applied", False)
        personality_adjustments = metadata.pop("personality_adjustments", [])

        return cls(
            response=data["response"],
            thread_id=data["thread_id"],
            raw_input=data["raw_input"],
            timestamp=data["timestamp"],
            raw_output=data.get("raw_output", data["response"]),
            tools_used=tools_used,
            memory_context_used=data.get("memory_context_used", False),
            memory_context=memory_context,
            use_tools=data.get("use_tools", True),
            use_memory=data.get("use_memory", True),
            error=data.get("error_message"),
            response_time_ms=response_time_ms,
            token_count=token_count,
            conversation_turn=conversation_turn,
            user_id=user_id,
            agent_personality_applied=agent_personality_applied,
            personality_adjustments=personality_adjustments,
            metadata=metadata,
            interaction_id=interaction_id,
        )

    def to_api_response(self) -> Dict[str, Any]:
        """
        Convert to API response format for your ChatResponse model.
        """
        return {
            "response": self.response,
            "thread_id": self.thread_id,
            "timestamp": self.timestamp,
            "tools_used": self.tools_used,
            "raw_input": self.raw_input,
            "raw_output": self.raw_output,
            "memory_context_used": self.memory_context_used,
            "entity_name": "Jade",  # From your config
        }

    def add_performance_metrics(
        self, response_time_ms: float, token_count: Optional[int] = None
    ):
        """Add performance metrics to the interaction"""
        self.response_time_ms = response_time_ms
        if token_count is not None:
            self.token_count = token_count

    def add_personality_adjustment(self, adjustment: str):
        """Track personality adjustments made to the response"""
        self.personality_adjustments.append(adjustment)
        self.agent_personality_applied = True

    def set_memory_context(self, context: str):
        """Set the memory context that was used"""
        self.memory_context = context
        self.memory_context_used = bool(context.strip())

    def add_metadata(self, key: str, value: Any):
        """Add custom metadata"""
        self.metadata[key] = value

    def get_summary(self) -> str:
        """Get a brief summary of the interaction"""
        summary_parts = [
            f"Thread: {self.thread_id}",
            f"Tools: {len(self.tools_used)}",
            f"Memory: {'Yes' if self.memory_context_used else 'No'}",
        ]

        if self.error:
            summary_parts.append("ERROR")

        if self.response_time_ms:
            summary_parts.append(f"{self.response_time_ms:.0f}ms")

        return f"[{' | '.join(summary_parts)}]"

    def __str__(self) -> str:
        """String representation for debugging"""
        return f"ChatInteraction({self.interaction_id[:8]}...): {self.raw_input[:50]}... -> {self.response[:50]}..."


@dataclass
class ConversationSummary:
    """
    Helper dataclass for conversation-level statistics and summaries.
    """

    thread_id: str
    total_interactions: int
    start_time: datetime
    last_interaction: datetime
    total_tools_used: int
    memory_usage_percentage: float
    common_topics: List[str] = field(default_factory=list)
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
