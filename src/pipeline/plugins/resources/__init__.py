"""Built-in resource plugins for the pipeline framework."""

<<<<<<< HEAD
from .http_llm_resource import HttpLLMResource
from .llm import UnifiedLLMResource
from .llm.providers import (ClaudeProvider, EchoProvider, GeminiProvider,
                            OllamaProvider, OpenAIProvider)
from .memory_resource import SimpleMemoryResource
from .postgres import (ConnectionPoolResource, PostgresPoolResource,
                       PostgresResource)
from .storage_backend import StorageBackend, StorageResource
=======
from .claude import ClaudeResource
from .echo_llm import EchoLLMResource
from .gemini import GeminiResource
from .llm_resource import LLMResource
from .memory_resource import SimpleMemoryResource
from .ollama_llm import OllamaLLMResource
from .openai import OpenAIResource
from .postgres import PostgresResource
>>>>>>> 5254d8c570961a7008f230d11e4766175159d40a
from .structured_logging import StructuredLogging
from .vector_memory import VectorMemoryResource

__all__ = [
    "LLMResource",
    "UnifiedLLMResource",
    "SimpleMemoryResource",
    "StructuredLogging",
    "StorageBackend",
    "StorageResource",
    "ConnectionPoolResource",
    "PostgresPoolResource",
    "PostgresResource",
    "VectorMemoryResource",
<<<<<<< HEAD
    "OpenAIProvider",
    "OllamaProvider",
    "GeminiProvider",
    "ClaudeProvider",
    "EchoProvider",
    "HttpLLMResource",
=======
    "OpenAIResource",
    "GeminiResource",
    "ClaudeResource",
>>>>>>> 5254d8c570961a7008f230d11e4766175159d40a
]
