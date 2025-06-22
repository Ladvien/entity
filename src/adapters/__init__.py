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


# In src/adapters/__init__.py
def create_adapters(config: EntityServerConfig) -> OutputAdapterManager:
    manager = OutputAdapterManager()

    for adapter_cfg in config.adapters:
        if adapter_cfg.type == "tts" and adapter_cfg.enabled:
            # Create TTSConfig from the main config, not adapter settings
            tts_adapter = TTSOutputAdapter(
                tts_config=config.tts,  # Use the main TTS config
                enabled=adapter_cfg.enabled,
            )
            manager.add_adapter(tts_adapter)
