"""Harmony Format LLM Infrastructure Adapter for GPT-OSS models.

This adapter implements support for OpenAI's harmony response format,
enabling Entity Framework to leverage GPT-OSS's multi-channel outputs
and advanced reasoning capabilities.
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Any, Dict, List, Optional

from .base import BaseInfrastructure


class ReasoningEffort(Enum):
    """Reasoning effort levels for GPT-OSS models."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Role(Enum):
    """Harmony format roles with hierarchy: system > developer > user > assistant > tool."""

    SYSTEM = "system"
    DEVELOPER = "developer"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class HarmonyChannel(Enum):
    """Output channels in harmony format."""

    ANALYSIS = "analysis"
    COMMENTARY = "commentary"
    FINAL = "final"


class HarmonyMessage:
    """Represents a message in harmony format."""

    def __init__(
        self, role: Role, content: str, channel: Optional[HarmonyChannel] = None
    ):
        self.role = role
        self.content = content
        self.channel = channel

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format."""
        msg = {"role": self.role.value, "content": self.content}
        if self.channel:
            msg["channel"] = self.channel.value
        return msg


class HarmonyOSSInfrastructure(BaseInfrastructure):
    """Infrastructure adapter for GPT-OSS models using harmony format.

    This adapter:
    - Formats prompts using the harmony multi-role structure
    - Parses multi-channel responses (analysis, commentary, final)
    - Maintains role hierarchy for proper context
    - Integrates with Entity's LLM infrastructure protocol
    """

    def __init__(
        self,
        model_path: str,
        reasoning_level: str = "medium",
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> None:
        """Initialize the Harmony OSS Infrastructure.

        Args:
            model_path: Path or identifier for the GPT-OSS model
            reasoning_level: Reasoning effort level (low, medium, high)
            temperature: Sampling temperature for generation
            max_tokens: Maximum tokens to generate
        """
        super().__init__()
        self.model_path = model_path
        self.reasoning_effort = ReasoningEffort(reasoning_level.lower())
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.conversation_history: List[HarmonyMessage] = []

    def _format_prompt_harmony(self, messages: List[HarmonyMessage]) -> str:
        """Format messages into harmony prompt structure.

        The harmony format enforces role hierarchy and supports
        multi-channel outputs for reasoning traces.
        """
        formatted = []

        role_priority = {
            Role.SYSTEM: 0,
            Role.DEVELOPER: 1,
            Role.USER: 2,
            Role.ASSISTANT: 3,
            Role.TOOL: 4,
        }

        sorted_messages = sorted(messages, key=lambda m: role_priority[m.role])

        for msg in sorted_messages:
            msg_dict = msg.to_dict()
            formatted.append(json.dumps(msg_dict))

        return "\n".join(formatted)

    def _parse_harmony_response(self, response: str) -> Dict[str, str]:
        """Parse multi-channel harmony response.

        Returns:
            Dictionary with channel names as keys and content as values
        """
        channels = {"analysis": "", "commentary": "", "final": ""}

        try:
            lines = response.strip().split("\n")
            current_channel = "final"

            for line in lines:
                if "<<ANALYSIS>>" in line:
                    current_channel = "analysis"
                    continue
                elif "<<COMMENTARY>>" in line:
                    current_channel = "commentary"
                    continue
                elif "<<FINAL>>" in line:
                    current_channel = "final"
                    continue
                else:
                    if line.strip():
                        channels[current_channel] += line.strip() + "\n"

        except Exception as e:
            self.logger.warning(f"Failed to parse harmony response: {e}")
            channels["final"] = response

        return {k: v.strip() for k, v in channels.items() if v.strip()}

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a response using harmony format.

        Args:
            prompt: User input prompt
            system_prompt: Optional system-level instructions

        Returns:
            Generated text response (final channel by default)
        """
        messages = []

        if system_prompt:
            messages.append(HarmonyMessage(Role.SYSTEM, system_prompt))

        messages.append(
            HarmonyMessage(
                Role.DEVELOPER,
                f"Use {self.reasoning_effort.value} reasoning effort. "
                f"Provide analysis and commentary channels when appropriate.",
            )
        )

        messages.append(HarmonyMessage(Role.USER, prompt))

        harmony_prompt = self._format_prompt_harmony(messages)

        response = await self._call_model(harmony_prompt)

        channels = self._parse_harmony_response(response)

        self.conversation_history.append(HarmonyMessage(Role.USER, prompt))
        self.conversation_history.append(
            HarmonyMessage(
                Role.ASSISTANT, channels.get("final", ""), HarmonyChannel.FINAL
            )
        )

        return channels.get("final", "")

    async def generate_with_channels(self, prompt: str) -> Dict[str, str]:
        """Generate response and return all channels.

        Returns:
            Dictionary with analysis, commentary, and final channels
        """
        messages = []
        messages.append(
            HarmonyMessage(
                Role.DEVELOPER,
                f"Use {self.reasoning_effort.value} reasoning. Return all channels.",
            )
        )
        messages.append(HarmonyMessage(Role.USER, prompt))

        harmony_prompt = self._format_prompt_harmony(messages)
        response = await self._call_model(harmony_prompt)

        return self._parse_harmony_response(response)

    async def _call_model(self, prompt: str) -> str:
        """Call the GPT-OSS model with harmony-formatted prompt.

        In production, this would integrate with the actual model API.
        For now, returns a simulated response.
        """
        self.logger.debug(f"Calling model with prompt length: {len(prompt)}")

        return """<<ANALYSIS>>
        The user is requesting assistance with a task.
        Context suggests this is part of a larger workflow.

        <<COMMENTARY>>
        This appears to be a straightforward request that can be handled
        using standard processing patterns.

        <<FINAL>>
        I understand your request and will process it accordingly."""

    async def health_check(self) -> bool:
        """Check if the GPT-OSS model is accessible and responsive."""
        try:
            response = await self.generate("test", "You are a test assistant")
            return bool(response)
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False

    async def startup(self) -> None:
        """Initialize the harmony infrastructure."""
        await super().startup()
        self.logger.info(
            f"Harmony OSS Infrastructure initialized with model: {self.model_path}, "
            f"reasoning: {self.reasoning_effort.value}"
        )

    async def shutdown(self) -> None:
        """Clean up resources."""
        self.conversation_history.clear()
        await super().shutdown()

    def set_reasoning_effort(self, level: str) -> None:
        """Dynamically adjust reasoning effort level."""
        self.reasoning_effort = ReasoningEffort(level.lower())
        self.logger.info(f"Reasoning effort set to: {self.reasoning_effort.value}")
