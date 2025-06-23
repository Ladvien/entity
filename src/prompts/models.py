# src/prompts/models.py
"""
Data models for prompt engineering - integrates with Entity's existing patterns
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class PromptTechnique(Enum):
    """Available prompt engineering techniques"""

    ZERO_SHOT = "zero_shot"
    FEW_SHOT = "few_shot"
    CHAIN_OF_THOUGHT = "chain_of_thought"
    SELF_CONSISTENCY = "self_consistency"
    PROMPT_CHAINING = "prompt_chaining"
    REACT = "react"
    TREE_OF_THOUGHTS = "tree_of_thoughts"
    GENERATE_KNOWLEDGE = "generate_knowledge"


@dataclass
class PromptExample:
    """Single example for few-shot learning"""

    input_text: str
    expected_output: str
    explanation: Optional[str] = None


@dataclass
class ExecutionContext:
    """Context for prompt execution - similar to Entity's ChatInteraction"""

    query: str
    thread_id: str = "default"
    additional_context: Dict[str, Any] = field(default_factory=dict)
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    use_memory: bool = True


@dataclass
class PromptConfiguration:
    """Configuration for a specific prompt technique"""

    technique_name: PromptTechnique
    template: str
    system_message: Optional[str] = None
    examples: List[PromptExample] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    temperature: float = 0.7
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """Result of prompt execution - similar to Entity's AgentResult"""

    generated_content: str
    technique_used: PromptTechnique
    execution_successful: bool
    execution_time_seconds: float
    thread_id: str
    timestamp: datetime
    token_count: Optional[int] = None
    confidence_score: Optional[float] = None
    intermediate_steps: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    memory_context: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
