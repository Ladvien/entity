# src/prompts/models.py

from enum import Enum


class PromptTechnique(str, Enum):
    """Advanced prompting techniques for detecting different types of queries"""

    # Basic reasoning
    CHAIN_OF_THOUGHT = "chain_of_thought"  # Step-by-step reasoning
    SELF_CONSISTENCY = "self_consistency"  # Multiple reasoning paths
    FEW_SHOT = "few_shot"  # Learning from examples

    # Direct approach
    DIRECT = "direct"  # Simple, direct prompting
