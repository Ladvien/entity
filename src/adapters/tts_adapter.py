# src/adapters/tts_adapter.py

import logging
import httpx
import json
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from src.service.config import TTSConfig
from src.shared.models import ChatInteraction

logger = logging.getLogger(__name__)


class TTSOutputAdapter:
    """
    TTS Output Adapter for Entity AI Agent

    Converts text responses to speech using Kokoro TTS API
    Designed specifically for Jade's sarcastic personality
    """

    def __init__(self, tts_config: TTSConfig, enabled: bool = True):
        self.config = tts_config
        self.enabled = enabled
        self.client = httpx.AsyncClient(timeout=30.0)

        # Create audio output directory
        self.audio_dir = Path("audio_output")
        self.audio_dir.mkdir(exist_ok=True)

        logger.info(f"✅ TTS Output Adapter initialized - Enabled: {enabled}")
        logger.info(f"🎙️ TTS Server: {tts_config.base_url}")
        logger.info(f"🔊 Voice: {tts_config.voice_name}")

    async def process_response(self, interaction: ChatInteraction) -> ChatInteraction:
        """
        Process a ChatInteraction and add TTS audio if enabled

        Args:
            interaction: The chat interaction to process

        Returns:
            ChatInteraction: Updated interaction with audio metadata
        """
        if not self.enabled:
            logger.debug("TTS adapter disabled, skipping audio generation")
            return interaction

        try:
            # Generate audio for the response
            audio_result = await self._synthesize_speech(
                text=interaction.response, thread_id=interaction.thread_id
            )

            if audio_result:
                # Add audio metadata to the interaction
                interaction.metadata.update(
                    {
                        "tts_enabled": True,
                        "audio_file_id": audio_result["audio_file_id"],
                        "audio_duration": audio_result.get("duration"),
                        "tts_voice": self.config.voice_name,
                        "tts_settings": {
                            "speed": self.config.speed,
                            "cfg_weight": self.config.cfg_weight,
                            "exaggeration": self.config.exaggeration,
                        },
                    }
                )

                logger.info(
                    f"🎵 Audio generated for interaction: {audio_result['audio_file_id']}"
                )
            else:
                interaction.metadata["tts_enabled"] = False
                interaction.metadata["tts_error"] = "Failed to generate audio"

        except Exception as e:
            logger.warning(f"⚠️ TTS processing failed: {e}")
            interaction.metadata.update({"tts_enabled": False, "tts_error": str(e)})

        return interaction

    async def _synthesize_speech(
        self, text: str, thread_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Synthesize speech using the Kokoro TTS API

        Args:
            text: Text to convert to speech
            thread_id: Thread ID for organization

        Returns:
            Dict with audio_file_id and other metadata, or None if failed
        """
        try:
            # Clean text for TTS (remove markdown, action descriptions, etc.)
            clean_text = self._clean_text_for_tts(text)

            if not clean_text.strip():
                logger.warning("No speech-worthy content after cleaning")
                return None

            # Prepare TTS request
            tts_request = {
                "text": clean_text,
                "voice_name": self.config.voice_name,
                "speed": self.config.speed,
                "cfg_weight": self.config.cfg_weight,
                "exaggeration": self.config.exaggeration,
                "output_format": self.config.output_format,
            }

            logger.debug(f"🎙️ TTS Request: {tts_request}")

            # Call TTS API
            response = await self.client.post(
                f"{self.config.base_url}/synthesize",
                json=tts_request,
                headers={"Content-Type": "application/json"},
            )

            response.raise_for_status()

            content_type = response.headers.get("content-type", "")

            if content_type.startswith("application/json"):
                result = response.json()
                logger.info(f"✅ TTS synthesis successful: {result}")
                return result

            elif content_type.startswith("audio/"):
                logger.info("✅ TTS synthesis successful (audio response)")
                return {
                    "audio_file_id": f"direct_{thread_id}",
                    "duration": None,
                    "raw_audio": response.content,
                }

            else:
                logger.warning(
                    f"⚠️ Unexpected content type from TTS server: {content_type}"
                )
                return {
                    "audio_file_id": f"direct_{thread_id}",
                    "duration": None,
                    "raw_audio": response.content,
                }

        except httpx.HTTPStatusError as e:
            logger.error(
                f"❌ TTS API error {e.response.status_code}: {e.response.text}"
            )
            return None
        except Exception as e:
            logger.exception(f"❌ TTS synthesis failed: {e}")
            return None

    def _clean_text_for_tts(self, text: str) -> str:
        """
        Clean text for TTS synthesis

        Removes:
        - Markdown formatting
        - Action descriptions in asterisks
        - Stage directions in parentheses
        - Excessive punctuation
        """
        import re

        # Remove markdown formatting
        text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)  # **bold**
        text = re.sub(r"\*(.*?)\*", r"\1", text)  # *italic*
        text = re.sub(r"`(.*?)`", r"\1", text)  # `code`

        # Remove action descriptions (things in asterisks that aren't emphasis)
        # Keep emotional indicators but remove action descriptions
        text = re.sub(
            r"\*([^*]*(?:rolls eyes|sarcastically|seething|reluctantly)[^*]*)\*",
            "",
            text,
        )
        text = re.sub(r"\*([^*]*(?:sighs|smirks|glares|shrugs)[^*]*)\*", "", text)

        # Remove stage directions in parentheses
        text = re.sub(r"\([^)]*\)", "", text)

        # Clean up extra spaces and newlines
        text = re.sub(r"\s+", " ", text)
        text = text.strip()

        # Ensure proper sentence endings for natural speech
        if text and not text.endswith((".", "!", "?")):
            text += "."

        return text

    async def get_audio_url(self, audio_file_id: str) -> str:
        """Get the URL to access generated audio"""
        return f"{self.config.base_url}/audio/{audio_file_id}"

    async def download_audio(
        self, audio_file_id: str, save_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Download audio file locally

        Args:
            audio_file_id: ID of the audio file
            save_path: Optional path to save file, auto-generated if None

        Returns:
            Path to downloaded file or None if failed
        """
        try:
            if save_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = (
                    f"jade_{timestamp}_{audio_file_id[:8]}.{self.config.output_format}"
                )
                save_path = self.audio_dir / filename

            # Download audio file
            response = await self.client.get(
                f"{self.config.base_url}/audio/{audio_file_id}"
            )
            response.raise_for_status()

            # Save to file
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(response.content)

            logger.info(f"🎵 Audio downloaded: {save_path}")
            return save_path

        except Exception as e:
            logger.error(f"❌ Audio download failed: {e}")
            return None

    async def test_connection(self) -> bool:
        """Test connection to TTS server"""
        try:
            response = await self.client.get(f"{self.config.base_url}/health")
            response.raise_for_status()
            health_data = response.json()

            logger.info(f"✅ TTS Server healthy: {health_data}")
            return True

        except Exception as e:
            logger.error(f"❌ TTS Server connection failed: {e}")
            return False

    async def list_available_voices(self) -> list:
        """Get list of available voices from TTS server"""
        try:
            response = await self.client.get(f"{self.config.base_url}/voices")
            response.raise_for_status()
            voices = response.json()

            logger.info(
                f"🎙️ Available voices: {[v.get('voice_name', v.get('name')) for v in voices]}"
            )
            return voices

        except Exception as e:
            logger.error(f"❌ Failed to get voices: {e}")
            return []

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
        logger.info("✅ TTS Output Adapter closed")

    def __del__(self):
        """Cleanup on deletion"""
        try:
            import asyncio

            if hasattr(self, "client"):
                asyncio.create_task(self.client.aclose())
        except:
            pass  # Best effort cleanup


class TTSResponse:
    """Helper class for TTS response data"""

    def __init__(
        self,
        audio_file_id: str,
        duration: Optional[float] = None,
        tts_adapter: Optional[TTSOutputAdapter] = None,
    ):
        self.audio_file_id = audio_file_id
        self.duration = duration
        self.tts_adapter = tts_adapter

    async def get_url(self) -> str:
        """Get URL to access the audio"""
        if self.tts_adapter:
            return await self.tts_adapter.get_audio_url(self.audio_file_id)
        return f"http://localhost:8888/audio/{self.audio_file_id}"  # Default fallback

    async def download(self, save_path: Optional[Path] = None) -> Optional[Path]:
        """Download the audio file"""
        if self.tts_adapter:
            return await self.tts_adapter.download_audio(self.audio_file_id, save_path)
        return None

    def __repr__(self):
        return f"TTSResponse(audio_file_id='{self.audio_file_id}', duration={self.duration})"
