from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from src.plugins.base import BaseToolPlugin
from src.shared.models import ChatInteraction
from math import tanh


# Define args_schema using Pydantic BaseModel for tools
class MemorySearchInput(BaseModel):
    query: str = Field(..., description="Search query")
    thread_id: Optional[str] = Field(
        default="default", description="Conversation thread ID"
    )
    limit: Optional[int] = Field(default=5, description="Number of results to return")


class StoreMemoryInput(BaseModel):
    content: str = Field(..., description="Memory content to store")
    thread_id: Optional[str] = Field(
        default="default", description="Conversation thread ID"
    )
    memory_type: Optional[str] = Field(
        default="observation", description="Type of memory"
    )
    importance_score: Optional[float] = Field(
        default=0.5, description="Relevance of the memory"
    )


# Implementing real tools by subclassing BaseToolPlugin
class MemorySearchTool(BaseToolPlugin):
    name = "memory_search"
    description = "Searches stored memories"
    args_schema = MemorySearchInput

    def get_context_injection(self, user_input, thread_id="default"):
        return {"query": user_input, "thread_id": thread_id}

    async def run(self, input_data: MemorySearchInput):
        # Simulate memory search logic
        return f"Search results for: {input_data.query}"


class StoreMemoryTool(BaseToolPlugin):
    name = "store_memory"
    description = "Stores a memory entry"
    args_schema = StoreMemoryInput

    def get_context_injection(
        self, user_input, thread_id="default", memory_type="observation"
    ):
        return {
            "memory_content": user_input,
            "thread_id": thread_id,
            "memory_type": memory_type,
        }

    async def run(self, input_data: StoreMemoryInput):
        # Simulate storing memory
        raw_score = input_data.importance_score
        normalized_score = (
            raw_score
            if 0.0 <= raw_score <= 1.0
            else max(0.0, min(1.0, tanh(raw_score)))
        )
        # Simulate saving interaction to memory system
        interaction = ChatInteraction(
            thread_id=input_data.thread_id,
            timestamp=datetime.utcnow(),
            raw_input="[STORED MEMORY]",
            raw_output=input_data.content,
            response=input_data.content,
            use_memory=True,
            metadata={
                "memory_type": input_data.memory_type,
                "importance_score": normalized_score,
                "source": "manual_storage",
            },
        )
        return f"Memory stored with importance: {normalized_score:.2f}"
