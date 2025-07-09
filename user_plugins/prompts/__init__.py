"""Expose example prompt plugins."""

from .chain_of_thought import ChainOfThoughtPrompt
from .complex_prompt import ComplexPrompt
from .intent_classifier import IntentClassifierPrompt
from .pii_scrubber import PIIScrubberPrompt
from .react_prompt import ReActPrompt

__all__ = [
    "IntentClassifierPrompt",
    "ReActPrompt",
    "ComplexPrompt",
    "ChainOfThoughtPrompt",
    "PIIScrubberPrompt",
]
