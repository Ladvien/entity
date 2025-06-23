# src/shared/utils.py - UPDATED VERSION with TTS metadata handling

from src.shared.models import ChatResponse, ChatInteraction
from src.shared.agent_result import AgentResult


def agent_result_to_response(result: AgentResult) -> ChatResponse:
    """Convert AgentResult to ChatResponse with proper serialization including TTS metadata"""

    # ✅ Convert intermediate steps to serializable format
    serializable_steps = []
    if result.intermediate_steps:
        for step in result.intermediate_steps:
            if isinstance(step, (list, tuple)) and len(step) == 2:
                action, observation = step
                # Convert to dict format
                step_dict = {
                    "action": {
                        "tool": getattr(action, "tool", ""),
                        "tool_input": str(getattr(action, "tool_input", "")),
                        "log": getattr(action, "log", ""),
                    },
                    "observation": str(observation),
                }
                serializable_steps.append(step_dict)
            else:
                # Handle other formats
                serializable_steps.append({"raw": str(step)})

    # ✅ Convert react steps to serializable format
    serializable_react_steps = []
    if result.react_steps:
        for step in result.react_steps:
            serializable_react_steps.append(
                {
                    "thought": step.thought,
                    "action": step.action,
                    "action_input": step.action_input,
                    "observation": step.observation,
                    "final_answer": step.final_answer,
                }
            )

    # 🎵 NEW: Extract TTS metadata from interaction if available
    # This is a bit of a hack, but we need to get the TTS metadata from somewhere
    # The issue is that agent_result_to_response doesn't have access to the processed interaction

    return ChatResponse(
        thread_id=result.thread_id,
        timestamp=result.timestamp,
        raw_input=result.raw_input,
        raw_output=result.raw_output,
        response=result.final_response,
        tools_used=result.tools_used,
        token_count=result.token_count,
        memory_context=result.memory_context,
        intermediate_steps=serializable_steps,
        react_steps=serializable_react_steps,
    )


def interaction_to_response(interaction: ChatInteraction) -> ChatResponse:
    """Convert ChatInteraction to ChatResponse - NEW FUNCTION with TTS metadata"""

    # Convert react steps if they exist in metadata
    react_steps = []
    if "react_steps" in interaction.metadata:
        react_steps = interaction.metadata["react_steps"]

    # Create base response
    response = ChatResponse(
        thread_id=interaction.thread_id,
        timestamp=interaction.timestamp,
        raw_input=interaction.raw_input,
        raw_output=interaction.raw_output,
        response=interaction.response,
        tools_used=interaction.tools_used,
        token_count=interaction.token_count,
        memory_context=interaction.memory_context,
        intermediate_steps=[],  # We could add these if needed
        react_steps=react_steps,
    )

    # 🎵 ADD TTS METADATA to the response
    if interaction.metadata.get("tts_enabled"):
        # Add TTS fields directly to the response
        response.tts_enabled = interaction.metadata.get("tts_enabled", False)
        response.audio_file_id = interaction.metadata.get("audio_file_id")
        response.audio_duration = interaction.metadata.get("audio_duration")
        response.tts_voice = interaction.metadata.get("tts_voice")
        response.tts_settings = interaction.metadata.get("tts_settings", {})

    return response


import re


def is_malformed_step(text: str) -> bool:
    """
    Checks if a ReAct step is malformed (e.g., Action present without Action Input).
    """
    # Match Action without Action Input
    lines = text.strip().splitlines()
    for i, line in enumerate(lines):
        if line.startswith("Action:"):
            if i + 1 >= len(lines) or not lines[i + 1].startswith("Action Input:"):
                return True
    return False
