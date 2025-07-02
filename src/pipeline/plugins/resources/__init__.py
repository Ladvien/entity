"""Built-in resource plugins for the pipeline framework."""

from .claude import ClaudeResource
from .echo_llm import EchoLLMResource
from .gemini import GeminiResource
from .llm_resource import LLMResource
from .memory_resource import SimpleMemoryResource
from .ollama_llm import OllamaLLMResource
from .openai import OpenAIResource
from .postgres import PostgresResource
from .structured_logging import StructuredLogging
from .vector_memory import VectorMemoryResource

__all__ = [
    "EchoLLMResource",
    "LLMResource",
    "OllamaLLMResource",
    "SimpleMemoryResource",
    "StructuredLogging",
    "PostgresResource",
    "VectorMemoryResource",
    "OpenAIResource",
    "GeminiResource",
    "ClaudeResource",
]
