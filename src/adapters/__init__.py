# src/adapters/__init__.py

from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import logging

from src.adapters.tts_adapter import TTSOutputAdapter
from src.core.config import EntityServerConfig
from src.shared.models import ChatInteraction

logger = logging.getLogger(__name__)


class BaseOutputAdapter(ABC):
    """Base class for output adapters"""

    @abstractmethod
    async def process_response(self, interaction: ChatInteraction) -> ChatInteraction:
        """Process a chat interaction and return the modified version"""
        pass

    @abstractmethod
    async def close(self):
        """Clean up adapter resources"""
        pass


class OutputAdapterManager:
    """Manages multiple output adapters"""

    def __init__(self):
        self.adapters: List[BaseOutputAdapter] = []
        self.enabled = True

    def add_adapter(self, adapter: BaseOutputAdapter):
        """Add an output adapter to the processing chain"""
        self.adapters.append(adapter)
        logger.info(f"✅ Added output adapter: {adapter.__class__.__name__}")

    async def process_interaction(
        self, interaction: ChatInteraction
    ) -> ChatInteraction:
        """Process interaction through all enabled adapters"""
        if not self.enabled or not self.adapters:
            return interaction

        processed_interaction = interaction

        for adapter in self.adapters:
            try:
                processed_interaction = await adapter.process_response(
                    processed_interaction
                )
                logger.debug(f"✅ Processed through {adapter.__class__.__name__}")
            except Exception as e:
                logger.error(
                    f"❌ Output adapter {adapter.__class__.__name__} failed: {e}"
                )
                # Continue with other adapters even if one fails

        return processed_interaction

    async def close_all(self):
        """Close all adapters"""
        for adapter in self.adapters:
            try:
                await adapter.close()
            except Exception as e:
                logger.error(f"Error closing adapter {adapter.__class__.__name__}: {e}")

        logger.info("✅ All output adapters closed")

    def enable(self):
        """Enable output adapter processing"""
        self.enabled = True
        logger.info("✅ Output adapters enabled")

    def disable(self):
        """Disable output adapter processing"""
        self.enabled = False
        logger.info("⏸️ Output adapters disabled")


def create_adapters(config: EntityServerConfig) -> OutputAdapterManager:
    """Create and configure output adapters based on config"""
    manager = OutputAdapterManager()

    # Process each adapter configuration
    for adapter_cfg in config.adapters:
        try:
            if adapter_cfg.type == "tts" and adapter_cfg.enabled:
                logger.info("🎙️ Creating TTS output adapter...")

                # Test TTS server connection first
                tts_adapter = TTSOutputAdapter(
                    tts_config=config.tts,
                    enabled=adapter_cfg.enabled,
                )

                # Add async connection test
                import asyncio

                try:
                    # Test connection during initialization
                    connection_test = asyncio.create_task(tts_adapter.test_connection())
                    # Don't await here to avoid blocking startup, but log intent
                    logger.info("🔍 TTS connection test scheduled")
                except Exception as e:
                    logger.warning(f"⚠️ Could not schedule TTS connection test: {e}")

                manager.add_adapter(tts_adapter)

            elif adapter_cfg.type == "webhook" and adapter_cfg.enabled:
                logger.info("🔗 Webhook adapter not implemented yet")
                # TODO: Implement webhook adapter

            elif adapter_cfg.type == "translation" and adapter_cfg.enabled:
                logger.info("🌍 Translation adapter not implemented yet")
                # TODO: Implement translation adapter

            elif adapter_cfg.type == "audio" and adapter_cfg.enabled:
                logger.info("🔊 Audio adapter not implemented yet")
                # TODO: Implement audio processing adapter

            else:
                logger.warning(f"⚠️ Unknown adapter type: {adapter_cfg.type}")

        except Exception as e:
            logger.error(f"❌ Failed to create {adapter_cfg.type} adapter: {e}")
            continue

    logger.info(f"✅ Created {len(manager.adapters)} output adapters")
    return manager
