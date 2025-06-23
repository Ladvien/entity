# src/prompts/config_manager.py
"""
Configuration manager for prompt techniques - integrates with Entity's config system
"""

import yaml
import logging
from typing import Dict, Optional
from pathlib import Path

from src.core.config import EntityServerConfig
from .models import PromptTechnique, PromptConfiguration, PromptExample

logger = logging.getLogger(__name__)


class PromptConfigManager:
    """Manages prompt configurations - integrates with Entity's config pattern"""

    def __init__(self, config_file_path: Optional[str] = None):
        self.config_file_path = config_file_path
        self.configurations: Dict[PromptTechnique, PromptConfiguration] = {}

        if config_file_path:
            self.load_configurations()

    @classmethod
    def from_entity_config(
        cls, entity_config: EntityServerConfig
    ) -> "PromptConfigManager":
        """Create from Entity's main configuration"""
        # Look for prompt_engineering section in Entity config
        prompt_config_path = getattr(entity_config, "prompt_engineering_config", None)
        if prompt_config_path:
            return cls(prompt_config_path)

        # Create with defaults
        manager = cls()
        manager._load_defaults()
        return manager

    def load_configurations(self):
        """Load configurations from YAML file"""
        if not self.config_file_path or not Path(self.config_file_path).exists():
            logger.warning(
                f"Prompt config file not found: {self.config_file_path}, using defaults"
            )
            self._load_defaults()
            return

        try:
            with open(self.config_file_path, "r") as file:
                config_data = yaml.safe_load(file)

            techniques_config = config_data.get("techniques", {})

            for technique_name, technique_config in techniques_config.items():
                try:
                    prompt_technique = PromptTechnique(technique_name)

                    # Parse examples
                    examples = []
                    for example_data in technique_config.get("examples", []):
                        if isinstance(example_data, dict):
                            examples.append(
                                PromptExample(
                                    input_text=example_data.get(
                                        "question", example_data.get("input", "")
                                    ),
                                    expected_output=example_data.get(
                                        "answer", example_data.get("output", "")
                                    ),
                                    explanation=example_data.get("explanation"),
                                )
                            )

                    configuration = PromptConfiguration(
                        technique_name=prompt_technique,
                        template=technique_config.get("template", ""),
                        system_message=technique_config.get("system_message"),
                        examples=examples,
                        parameters=technique_config.get("parameters", {}),
                        temperature=technique_config.get("temperature", 0.7),
                        metadata=technique_config.get("metadata", {}),
                    )

                    self.configurations[prompt_technique] = configuration
                    logger.info(f"✅ Loaded prompt technique: {technique_name}")

                except ValueError as e:
                    logger.warning(f"Unknown technique '{technique_name}': {e}")

        except Exception as e:
            logger.error(f"Failed to load prompt configurations: {e}")
            self._load_defaults()

    def _load_defaults(self):
        """Load default configurations"""
        defaults = {
            PromptTechnique.ZERO_SHOT: PromptConfiguration(
                technique_name=PromptTechnique.ZERO_SHOT,
                template="{system_message}\n\nQuestion: {query}\n\nAnswer:",
                system_message="You are a helpful AI assistant.",
            ),
            PromptTechnique.CHAIN_OF_THOUGHT: PromptConfiguration(
                technique_name=PromptTechnique.CHAIN_OF_THOUGHT,
                template="{system_message}\n\nQuestion: {query}\n\n{reasoning_instruction}",
                system_message="You are a logical reasoning assistant.",
                parameters={"reasoning_instruction": "Let's think step by step:"},
            ),
            PromptTechnique.FEW_SHOT: PromptConfiguration(
                technique_name=PromptTechnique.FEW_SHOT,
                template="{system_message}\n\nExamples:\n{examples}\n\nQuestion: {query}\nAnswer:",
                system_message="You are a helpful AI assistant. Follow the examples provided.",
                examples=[
                    PromptExample("What is 2+2?", "2+2 equals 4"),
                    PromptExample(
                        "What is the capital of France?",
                        "The capital of France is Paris",
                    ),
                ],
            ),
        }

        self.configurations.update(defaults)
        logger.info(f"✅ Loaded {len(defaults)} default prompt configurations")

    def get_configuration(
        self, technique: PromptTechnique
    ) -> Optional[PromptConfiguration]:
        """Get configuration for specific technique"""
        return self.configurations.get(technique)

    def get_all_configurations(self) -> Dict[PromptTechnique, PromptConfiguration]:
        """Get all loaded configurations"""
        return self.configurations.copy()
