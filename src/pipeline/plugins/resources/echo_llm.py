from __future__ import annotations

from pipeline.resources.llm import LLMResource


class EchoLLMResource(LLMResource):
    """Return the provided prompt unchanged.

    This resource is primarily useful for testing or for demos where an
    immediate echo response is desirable. It exposes no configuration
    options and does not interact with external services.
    """

    name = "echo"
    aliases = ["llm"]

    async def _execute_impl(self, context):
        """No-op execution hook required by :class:`LLMResource`."""
        return None

    async def generate(self, prompt: str) -> str:
        """Echo ``prompt`` back to the caller.

        Args:
            prompt: User provided prompt text.

        Returns:
            The original ``prompt`` without modification.
        """

        return prompt

    __call__ = generate
