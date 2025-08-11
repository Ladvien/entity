"""Example plugin demonstrating type-safe dependency injection."""

from __future__ import annotations

from typing import Any, Dict

from entity.plugins.typed_base import LLMMemoryPlugin, LLMProtocol, MemoryProtocol
from pydantic import BaseModel, Field


class TypedExamplePlugin(LLMMemoryPlugin):
    """Example plugin using type-safe dependency injection.

    This plugin demonstrates:
    - Type-safe LLM and Memory injection
    - Configuration validation with Pydantic
    - Proper async/await patterns
    - IDE autocomplete support
    """

    class ConfigModel(BaseModel):
        """Configuration model with validation."""

        max_retries: int = Field(default=3, ge=1, le=10)
        temperature: float = Field(default=0.7, ge=0.0, le=1.0)
        store_responses: bool = Field(default=True)
        response_prefix: str = Field(default="Response: ")

        class Config:
            extra = "forbid"

    supported_stages = ["think", "respond"]

    def __init__(
        self,
        resources: Dict[str, Any],
        config: Dict[str, Any] | None = None,
        *,
        llm: LLMProtocol,  # Type-safe LLM injection
        memory: MemoryProtocol,  # Type-safe Memory injection
    ):
        """Initialize with type-safe dependencies.

        Args:
            resources: Resource dictionary for compatibility
            config: Plugin configuration
            llm: LLM resource with full type safety
            memory: Memory resource with full type safety
        """
        super().__init__(resources, config, llm=llm, memory=memory)

        # Resources are now fully typed - IDE provides autocomplete!
        # self.llm: LLMProtocol
        # self.memory: MemoryProtocol

    async def _execute_impl(self, context: Any) -> str:
        """Execute the plugin with type safety.

        Demonstrates:
        - Type-safe resource access
        - Configuration usage
        - Error handling
        - Memory operations
        """
        config = self.config  # Typed configuration

        # Build prompt with configuration
        prompt = f"Please respond to: {context.text}"

        # Type-safe LLM generation with retry logic
        response = await self._generate_with_retries(prompt, config.max_retries)

        # Type-safe memory storage (if configured)
        if config.store_responses:
            await self._store_response(context, response)

        # Return formatted response
        return f"{config.response_prefix}{response}"

    async def _generate_with_retries(self, prompt: str, max_retries: int) -> str:
        """Generate response with retry logic.

        Demonstrates type-safe LLM usage with error handling.
        """
        for attempt in range(max_retries):
            try:
                # IDE provides autocomplete for generate method!
                response = await self.llm.generate(prompt)

                if response and response.strip():
                    return response.strip()

            except Exception as e:
                if attempt == max_retries - 1:
                    # Last attempt failed
                    raise RuntimeError(
                        f"LLM generation failed after {max_retries} attempts"
                    ) from e

                # Log retry attempt (IDE knows this method exists)
                if self.llm.health_check():
                    continue
                else:
                    raise RuntimeError("LLM health check failed") from e

        raise RuntimeError("Failed to generate response")

    async def _store_response(self, context: Any, response: str) -> None:
        """Store response in memory with type safety.

        Demonstrates type-safe memory operations.
        """
        # Create storage key
        user_id = getattr(context, "user_id", "unknown")
        timestamp = getattr(context, "timestamp", "unknown")
        key = f"response:{user_id}:{timestamp}"

        # Type-safe memory storage - IDE provides autocomplete!
        response_data = {
            "response": response,
            "user_id": user_id,
            "timestamp": timestamp,
            "plugin": self.__class__.__name__,
        }

        await self.memory.store(key, response_data)

        # Update response counter
        counter_key = f"counter:{user_id}"
        current_count = await self.memory.load(counter_key, 0)
        await self.memory.store(counter_key, current_count + 1)

    def validate_health(self) -> bool:
        """Validate that all dependencies are healthy.

        Demonstrates type-safe health checking.
        """
        # IDE provides autocomplete for health_check methods
        return self.llm.health_check() and self.memory.health_check()

    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user statistics from memory.

        Demonstrates type-safe memory retrieval operations.
        """
        # Type-safe memory access
        counter_key = f"counter:{user_id}"
        response_count = await self.memory.load(counter_key, 0)

        return {
            "user_id": user_id,
            "total_responses": response_count,
            "plugin_name": self.__class__.__name__,
            "llm_healthy": self.llm.health_check(),
            "memory_healthy": self.memory.health_check(),
        }
