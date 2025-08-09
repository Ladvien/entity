"""Unit tests for HarmonyOSSInfrastructure adapter."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from entity.infrastructure.harmony_oss_infra import (
    HarmonyChannel,
    HarmonyMessage,
    HarmonyOSSInfrastructure,
    ReasoningEffort,
    Role,
)


class TestHarmonyMessage:
    """Test HarmonyMessage class."""

    def test_message_creation(self):
        """Test creating a harmony message."""
        msg = HarmonyMessage(Role.USER, "Hello")
        assert msg.role == Role.USER
        assert msg.content == "Hello"
        assert msg.channel is None

    def test_message_with_channel(self):
        """Test message with channel specified."""
        msg = HarmonyMessage(Role.ASSISTANT, "Response", HarmonyChannel.FINAL)
        assert msg.channel == HarmonyChannel.FINAL

    def test_message_to_dict(self):
        """Test converting message to dictionary."""
        msg = HarmonyMessage(Role.SYSTEM, "Instructions")
        result = msg.to_dict()
        assert result == {"role": "system", "content": "Instructions"}

    def test_message_to_dict_with_channel(self):
        """Test converting message with channel to dictionary."""
        msg = HarmonyMessage(Role.ASSISTANT, "Analysis", HarmonyChannel.ANALYSIS)
        result = msg.to_dict()
        assert result == {
            "role": "assistant",
            "content": "Analysis",
            "channel": "analysis",
        }


class TestHarmonyOSSInfrastructure:
    """Test HarmonyOSSInfrastructure class."""

    @pytest.fixture
    def infra(self):
        """Create a test infrastructure instance."""
        return HarmonyOSSInfrastructure(
            model_path="test-model",
            reasoning_level="medium",
            temperature=0.7,
            max_tokens=2000,
        )

    def test_initialization(self, infra):
        """Test infrastructure initialization."""
        assert infra.model_path == "test-model"
        assert infra.reasoning_effort == ReasoningEffort.MEDIUM
        assert infra.temperature == 0.7
        assert infra.max_tokens == 2000
        assert infra.conversation_history == []

    def test_reasoning_effort_levels(self):
        """Test different reasoning effort levels."""
        low = HarmonyOSSInfrastructure("model", reasoning_level="low")
        assert low.reasoning_effort == ReasoningEffort.LOW

        high = HarmonyOSSInfrastructure("model", reasoning_level="HIGH")
        assert high.reasoning_effort == ReasoningEffort.HIGH

    def test_format_prompt_harmony(self, infra):
        """Test formatting messages to harmony prompt."""
        messages = [
            HarmonyMessage(Role.USER, "Question"),
            HarmonyMessage(Role.SYSTEM, "System prompt"),
            HarmonyMessage(Role.DEVELOPER, "Dev instructions"),
        ]

        result = infra._format_prompt_harmony(messages)
        lines = result.split("\n")

        # Check role hierarchy (system > developer > user)
        assert json.loads(lines[0])["role"] == "system"
        assert json.loads(lines[1])["role"] == "developer"
        assert json.loads(lines[2])["role"] == "user"

    def test_parse_harmony_response_multi_channel(self, infra):
        """Test parsing multi-channel harmony response."""
        response = """<<ANALYSIS>>
        This is the analysis section.
        Multiple lines here.

        <<COMMENTARY>>
        Commentary about the analysis.

        <<FINAL>>
        The final response to the user."""

        result = infra._parse_harmony_response(response)

        assert "analysis" in result
        assert "This is the analysis section" in result["analysis"]
        assert "Commentary about the analysis" in result["commentary"]
        assert "The final response to the user" in result["final"]

    def test_parse_harmony_response_single_channel(self, infra):
        """Test parsing response with only final channel."""
        response = "Simple response without channels"

        result = infra._parse_harmony_response(response)

        assert result["final"] == "Simple response without channels"
        assert "analysis" not in result or result["analysis"] == ""

    def test_parse_harmony_response_malformed(self, infra):
        """Test parsing malformed response falls back gracefully."""
        response = "<<INVALID>>\nSome content\n<<UNKNOWN>>\nMore content"

        result = infra._parse_harmony_response(response)

        # Should put everything in final channel
        assert "<<INVALID>>" in result["final"]

    @pytest.mark.asyncio
    async def test_generate_basic(self, infra):
        """Test basic generation flow."""
        with patch.object(infra, "_call_model", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = "<<FINAL>>\nTest response"

            result = await infra.generate("Test prompt")

            assert result == "Test response"
            assert len(infra.conversation_history) == 2
            assert infra.conversation_history[0].role == Role.USER
            assert infra.conversation_history[1].role == Role.ASSISTANT

    @pytest.mark.asyncio
    async def test_generate_with_system_prompt(self, infra):
        """Test generation with system prompt."""
        with patch.object(infra, "_call_model", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = "<<FINAL>>\nResponse"

            await infra.generate("Prompt", "System instructions")

            # Check that system prompt was included
            call_args = mock_call.call_args[0][0]
            assert "system" in call_args
            assert "System instructions" in call_args

    @pytest.mark.asyncio
    async def test_generate_with_channels(self, infra):
        """Test getting all channels from generation."""
        with patch.object(infra, "_call_model", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = """<<ANALYSIS>>
            Analysis content
            <<COMMENTARY>>
            Commentary content
            <<FINAL>>
            Final content"""

            result = await infra.generate_with_channels("Test")

            assert result["analysis"] == "Analysis content"
            assert result["commentary"] == "Commentary content"
            assert result["final"] == "Final content"

    def test_set_reasoning_effort(self, infra):
        """Test dynamically changing reasoning effort."""
        assert infra.reasoning_effort == ReasoningEffort.MEDIUM

        infra.set_reasoning_effort("high")
        assert infra.reasoning_effort == ReasoningEffort.HIGH

        infra.set_reasoning_effort("LOW")
        assert infra.reasoning_effort == ReasoningEffort.LOW

    @pytest.mark.asyncio
    async def test_health_check_success(self, infra):
        """Test successful health check."""
        with patch.object(infra, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "Test response"

            result = await infra.health_check()

            assert result is True
            mock_gen.assert_called_once_with("test", "You are a test assistant")

    @pytest.mark.asyncio
    async def test_health_check_failure(self, infra):
        """Test failed health check."""
        with patch.object(infra, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.side_effect = Exception("Connection failed")

            result = await infra.health_check()

            assert result is False

    @pytest.mark.asyncio
    async def test_startup(self, infra):
        """Test infrastructure startup."""
        with patch.object(infra.logger, "info") as mock_log:
            await infra.startup()

            mock_log.assert_called()
            call_args = mock_log.call_args[0][0]
            assert "model: test-model" in call_args
            assert "reasoning: medium" in call_args

    @pytest.mark.asyncio
    async def test_shutdown(self, infra):
        """Test infrastructure shutdown clears history."""
        # Add some history
        infra.conversation_history.append(HarmonyMessage(Role.USER, "Test"))
        assert len(infra.conversation_history) == 1

        await infra.shutdown()

        assert len(infra.conversation_history) == 0

    def test_role_hierarchy(self, infra):
        """Test that role hierarchy is maintained correctly."""
        messages = [
            HarmonyMessage(Role.TOOL, "Tool msg"),
            HarmonyMessage(Role.USER, "User msg"),
            HarmonyMessage(Role.SYSTEM, "System msg"),
            HarmonyMessage(Role.ASSISTANT, "Assistant msg"),
            HarmonyMessage(Role.DEVELOPER, "Dev msg"),
        ]

        result = infra._format_prompt_harmony(messages)
        lines = result.split("\n")

        # Verify order: system > developer > user > assistant > tool
        roles = [json.loads(line)["role"] for line in lines]
        assert roles == ["system", "developer", "user", "assistant", "tool"]
