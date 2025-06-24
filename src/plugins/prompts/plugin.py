# src/plugins/prompts/base.py

from abc import ABC, abstractmethod
from typing import Any, Dict, Set, Type
from pydantic import BaseModel
from langchain_core.tools import StructuredTool

# Import the supporting classes
from .context import PromptContext
from .validation import ValidationResult


class PromptPlugin(ABC):
    """Base class for all prompt plugins"""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the plugin with optional configuration"""
        self.config = config or {}
        self.name = self.__class__.__name__.lower().replace("plugin", "")

    @abstractmethod
    def generate_prompt(self, context: PromptContext) -> str:
        """Generate a prompt based on the provided context."""
        ...

    @abstractmethod
    def validate_prompt(self) -> ValidationResult:
        """Validate the prompt structure and content."""
        ...

    @abstractmethod
    def get_required_variables(self) -> Set[str]:
        """Get a set of required variables for the prompt."""
        ...

    def get_optional_variables(self) -> Set[str]:
        """Get a set of optional variables for the prompt."""
        return set()

    def get_strategy_name(self) -> str:
        """Get the name of this prompt strategy"""
        return self.name

    def supports_tools(self) -> bool:
        """Whether this plugin supports tool usage"""
        return True

    def get_max_iterations(self) -> int:
        """Get recommended max iterations for this strategy"""
        return 10

    def preprocess_context(self, context: PromptContext) -> PromptContext:
        """Preprocess the context before prompt generation (override if needed)"""
        return context

    def postprocess_prompt(self, prompt: str, context: PromptContext) -> str:
        """Postprocess the generated prompt (override if needed)"""
        return prompt
