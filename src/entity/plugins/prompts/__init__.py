"""Built-in reasoning prompt plugins."""

from .chain_of_thought import ChainOfThoughtPrompt
from .react import ReActPrompt

__all__ = ["ChainOfThoughtPrompt", "ReActPrompt"]
