from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class PromptTechnique(Enum):
    """Available prompt engineering techniques"""

    ZERO_SHOT = "zero_shot"
    FEW_SHOT = "few_shot"
    CHAIN_OF_THOUGHT = "chain_of_thought"
    SELF_CONSISTENCY = "self_consistency"
    PROMPT_CHAINING = "prompt_chaining"
    REACT = "react"
    META_PROMPTING = "meta_prompting"
    TREE_OF_THOUGHTS = "tree_of_thoughts"
    GENERATE_KNOWLEDGE = "generate_knowledge"
    REFLEXION = "reflexion"
    PROGRAM_AIDED = "program_aided"
    MULTIMODAL_COT = "multimodal_cot"
    DIRECTIONAL_STIMULUS = "directional_stimulus"
    ACTIVE_PROMPT = "active_prompt"


@dataclass
class PromptExample:
    """Single example for few-shot learning"""

    input_text: str
    expected_output: str
    explanation: Optional[str] = None


@dataclass
class ExecutionContext:
    """Context passed to prompt execution"""

    query: str
    additional_context: Dict[str, Any] = field(default_factory=dict)
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    timeout_seconds: Optional[float] = None


@dataclass
class PromptConfiguration:
    """Configuration for a specific prompt technique"""

    technique_name: PromptTechnique
    template: str
    system_message: Optional[str] = None
    examples: List[PromptExample] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    validation_rules: List[str] = field(default_factory=list)
    max_retries: int = 3
    temperature: float = 0.7
    timeout_seconds: float = 30.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """Result of prompt execution"""

    generated_content: str
    technique_used: PromptTechnique
    execution_successful: bool
    execution_time_seconds: float
    token_count: Optional[int] = None
    confidence_score: Optional[float] = None
    intermediate_steps: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChainStep:
    """Single step in prompt chaining"""

    step_name: str
    step_template: str
    step_parameters: Dict[str, Any] = field(default_factory=dict)
