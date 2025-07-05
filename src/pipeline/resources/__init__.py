"""Public resource wrappers for pipeline consumers."""

from interfaces.resources import LLM, BaseResource, LLMResource, Resource

from .container import ResourceContainer
from .llm.unified import UnifiedLLMResource
from .memory_resource import MemoryResource, SimpleMemoryResource

__all__ = [
    "MemoryResource",
    "SimpleMemoryResource",
    "UnifiedLLMResource",
    "ResourceContainer",
    "LLM",
    "LLMResource",
    "Resource",
    "BaseResource",
]
