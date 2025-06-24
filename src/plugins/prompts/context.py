# src/plugins/prompts/context.py

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool


class PromptContext(BaseModel):
    """Context information for generating prompts dynamically"""

    # Core agent information
    personality: Any  # EntityConfig object
    tools: List[StructuredTool] = Field(default_factory=list)
    memory_config: Any = None  # MemoryConfig object

    # Dynamic variables
    custom_variables: Dict[str, Any] = Field(default_factory=dict)

    # Runtime context
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    previous_messages: List[str] = Field(default_factory=list)

    # Performance hints
    reasoning_mode: str = "standard"  # standard, detailed, fast
    max_tokens: Optional[int] = None
    temperature_override: Optional[float] = None

    class Config:
        arbitrary_types_allowed = True  # Allow non-Pydantic types like EntityConfig

    def get_personality_vars(self) -> Dict[str, Any]:
        """Extract personality variables for template substitution"""
        if not self.personality:
            return {}

        return {
            "name": getattr(self.personality, "name", "Assistant"),
            "entity_id": getattr(self.personality, "entity_id", "agent"),
            "sarcasm_level": getattr(self.personality, "sarcasm_level", 0.5),
            "loyalty_level": getattr(self.personality, "loyalty_level", 0.5),
            "anger_level": getattr(self.personality, "anger_level", 0.5),
            "wit_level": getattr(self.personality, "wit_level", 0.5),
            "response_brevity": getattr(self.personality, "response_brevity", 0.5),
            "memory_influence": getattr(self.personality, "memory_influence", 0.5),
        }

    def get_tool_names(self) -> List[str]:
        """Get list of available tool names"""
        return [tool.name for tool in self.tools]

    def get_tool_descriptions(self) -> str:
        """Get formatted tool descriptions for prompt"""
        if not self.tools:
            return "No tools available."

        descriptions = []
        for tool in self.tools:
            desc = f"- **{tool.name}**: {tool.description}"
            descriptions.append(desc)
        return "\n".join(descriptions)
