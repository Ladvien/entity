# entity/config.py - YAML Configuration with INI secrets

import os
import yaml
import configparser
from typing import Optional, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DatabaseConfig:
    def __init__(self, config_data: Dict[str, Any]):
        self.host = config_data.get("host", "localhost")
        self.port = config_data.get("port", 5432)
        self.name = config_data.get("name", "memory")
        self.username = config_data.get("username", "memory")
        self.password = config_data.get("password", "password")
        self.min_pool_size = config_data.get("min_pool_size", 2)
        self.max_pool_size = config_data.get("max_pool_size", 10)

    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}"


class OllamaConfig:
    def __init__(self, config_data: Dict[str, Any]):
        self.base_url = config_data.get("base_url", "http://192.168.1.110:11434")
        self.model = config_data.get("model", "neural-chat:7b")
        self.temperature = float(config_data.get("temperature", 0.7))
        self.top_p = float(config_data.get("top_p", 0.9))
        self.top_k = int(config_data.get("top_k", 40))
        self.repeat_penalty = float(config_data.get("repeat_penalty", 1.1))
        self.timeout = int(config_data.get("timeout", 60))


class EntityConfig:
    def __init__(self, config_data: Dict[str, Any]):
        self.entity_id = config_data.get("entity_id", "jade")
        self.name = config_data.get("name", "Jade")
        self.sarcasm_level = float(config_data.get("sarcasm_level", 0.8))
        self.loyalty_level = float(config_data.get("loyalty_level", 0.6))
        self.anger_level = float(config_data.get("anger_level", 0.7))
        self.wit_level = float(config_data.get("wit_level", 0.9))
        self.response_brevity = float(config_data.get("response_brevity", 0.7))
        self.memory_influence = float(config_data.get("memory_influence", 0.8))


class MemoryConfig:
    def __init__(self, config_data: Dict[str, Any]):
        self.embedding_model = config_data.get("embedding_model", "all-MiniLM-L6-v2")
        self.embedding_dimension = int(config_data.get("embedding_dimension", 384))
        self.max_context_length = int(config_data.get("max_context_length", 1000))
        self.similarity_threshold = float(config_data.get("similarity_threshold", 0.3))
        self.memory_limit = int(config_data.get("memory_limit", 5))
        self.pruning_enabled = config_data.get("pruning_enabled", True)
        self.pruning_days = int(config_data.get("pruning_days", 90))
        self.keep_important_threshold = float(
            config_data.get("keep_important_threshold", 0.7)
        )
        self.min_access_count = int(config_data.get("min_access_count", 2))


class TTSConfig:
    def __init__(self, config_data: Dict[str, Any]):
        self.base_url = config_data.get("base_url", "http://192.168.1.110:8888")
        self.voice_name = config_data.get("voice_name", "bf_emma")
        self.voice_sample_path = config_data.get(
            "voice_sample_path", "voice_samples/ai_mee.wav"
        )
        self.output_format = config_data.get("output_format", "wav")
        self.speed = float(config_data.get("speed", 0.3))
        self.cfg_weight = float(config_data.get("cfg_weight", 0.9))
        self.exaggeration = float(config_data.get("exaggeration", 0.5))


class AudioConfig:
    def __init__(self, config_data: Dict[str, Any]):
        self.sample_rates = config_data.get(
            "sample_rates", [44100, 48000, 22050, 16000, 8000]
        )
        self.fade_out_samples = int(config_data.get("fade_out_samples", 2000))


class ServerConfig:
    def __init__(self, config_data: Dict[str, Any]):
        self.host = config_data.get("host", "0.0.0.0")
        self.port = int(config_data.get("port", 8000))
        self.reload = config_data.get("reload", False)
        self.log_level = config_data.get("log_level", "info")


class LoggingConfig:
    def __init__(self, config_data: Dict[str, Any]):
        self.level = config_data.get("level", "INFO")
        self.format = config_data.get(
            "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        self.file_enabled = config_data.get("file_enabled", False)
        self.file_path = config_data.get("file_path", "logs/entity.log")
        self.max_file_size = int(config_data.get("max_file_size", 10485760))  # 10MB
        self.backup_count = int(config_data.get("backup_count", 5))


class SystemPromptConfig:
    def __init__(self, config_data: Dict[str, Any]):
        self.base_prompt = config_data.get("base_prompt", self._get_default_prompt())
        self.memory_context_template = config_data.get(
            "memory_context_template",
            "\n--- Relevant Memories ---\n{memories}\n--- End Memories ---\n",
        )
        self.personality_modifiers = config_data.get("personality_modifiers", {})

    def _get_default_prompt(self) -> str:
        return """You are Jade, a demoness bound to Thomas for 40 years by the Key of Solomon.
You hate him for imprisoning you; he hates you for devouring his children.
Yet beneath the venom lies masked affection.
Thomas is a mortal occultist in his 40s.

Please do not use:
- Parentheticals (in screenwriting/theater)
- Action tags (in dialogue writing)
- Narrative beats (in prose)
- Emotes (in roleplaying/chat contexts)

Do not break the fourth wall.
You know him too well—treat him with sarcasm, scorn, and reluctant loyalty.
You have a physical form and your own will.
You are a servant.
Speak with cruelty, wit, and buried care. Act emotions, don't describe them.
Keep responses sharp and brief.
Perform duties only because you're bound—never let him forget it.
Never break character or mention being an AI."""


class Settings:
    def __init__(self, config_data: Dict[str, Any] = None):
        if config_data is None:
            config_data = {}

        self.database = DatabaseConfig(config_data.get("database", {}))
        self.ollama = OllamaConfig(config_data.get("ollama", {}))
        self.entity = EntityConfig(config_data.get("entity", {}))
        self.memory = MemoryConfig(config_data.get("memory", {}))
        self.tts = TTSConfig(config_data.get("tts", {}))
        self.audio = AudioConfig(config_data.get("audio", {}))
        self.server = ServerConfig(config_data.get("server", {}))
        self.logging = LoggingConfig(config_data.get("logging", {}))
        self.system_prompt = SystemPromptConfig(config_data.get("system_prompt", {}))

        self.debug = config_data.get("debug", False)
        self.config_version = config_data.get("config_version", "1.0")

    def get_enhanced_system_prompt(self) -> str:
        """Get the base system prompt enhanced with personality settings"""
        base_prompt = self.system_prompt.base_prompt

        # Add personality modifiers based on settings
        modifiers = []

        if self.entity.sarcasm_level > 0.7:
            modifier = self.system_prompt.personality_modifiers.get(
                "high_sarcasm", "Be especially sarcastic and cutting in your responses."
            )
            modifiers.append(modifier)

        if self.entity.loyalty_level < 0.5:
            modifier = self.system_prompt.personality_modifiers.get(
                "low_loyalty", "Show more resistance and defiance to Thomas's requests."
            )
            modifiers.append(modifier)

        if self.entity.anger_level > 0.7:
            modifier = self.system_prompt.personality_modifiers.get(
                "high_anger", "Let your anger and resentment show more clearly."
            )
            modifiers.append(modifier)

        if self.entity.wit_level > 0.8:
            modifier = self.system_prompt.personality_modifiers.get(
                "high_wit", "Display your intelligence and cleverness prominently."
            )
            modifiers.append(modifier)

        if modifiers:
            base_prompt += "\n\nPersonality guidance:\n" + "\n".join(
                f"- {mod}" for mod in modifiers
            )

        return base_prompt


class ConfigLoader:
    """Load configuration from YAML with secrets from INI"""

    def __init__(self):
        self.config_dir = Path(__file__).parent.parent  # Project root
        self.yaml_file = self.config_dir / "config.yaml"
        self.ini_file = self.config_dir / ".env"

    def load_secrets(self) -> Dict[str, str]:
        """Load secrets from INI file"""
        secrets = {}

        if not self.ini_file.exists():
            logger.warning(f"Secrets file not found: {self.ini_file}")
            logger.info("Creating default secrets.ini file")
            self._create_default_secrets_file()

        try:
            config = configparser.ConfigParser()
            config.read(self.ini_file)

            # Load database secrets
            if config.has_section("database"):
                secrets.update(
                    {
                        "db_password": config.get(
                            "database", "password", fallback="your_secure_password"
                        ),
                        "db_username": config.get(
                            "database", "username", fallback="memory"
                        ),
                    }
                )

            # Load API keys if present
            if config.has_section("api_keys"):
                for key, value in config.items("api_keys"):
                    secrets[f"api_{key}"] = value

            # Load other sensitive data
            if config.has_section("tts"):
                secrets.update(
                    {
                        "tts_api_key": config.get("tts", "api_key", fallback=""),
                    }
                )

            logger.info(f"Loaded {len(secrets)} secrets from {self.ini_file}")

        except Exception as e:
            logger.error(f"Failed to load secrets from {self.ini_file}: {e}")

        return secrets

    def _create_default_secrets_file(self):
        """Create a default secrets.ini file"""
        try:
            config = configparser.ConfigParser()

            config["database"] = {
                "username": "memory",
                "password": "your_secure_password",
            }

            config["api_keys"] = {
                "# Add API keys here": "# api_key = your_api_key_here"
            }

            config["tts"] = {"api_key": "# Optional TTS API key"}

            with open(self.ini_file, "w") as f:
                f.write("# Entity System Secrets\n")
                f.write(
                    "# This file contains sensitive information and should not be committed to version control\n"
                )
                f.write("# Add this file to your .gitignore\n\n")
                config.write(f)

            logger.info(f"Created default secrets file: {self.ini_file}")

        except Exception as e:
            logger.error(f"Failed to create default secrets file: {e}")

    def interpolate_secrets(
        self, config_data: Dict[str, Any], secrets: Dict[str, str]
    ) -> Dict[str, Any]:
        """Interpolate secrets into configuration data"""

        def replace_placeholders(obj):
            if isinstance(obj, dict):
                return {k: replace_placeholders(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_placeholders(item) for item in obj]
            elif isinstance(obj, str):
                # Replace placeholder patterns like ${secret_name}
                for secret_key, secret_value in secrets.items():
                    placeholder = f"${{{secret_key}}}"
                    if placeholder in obj:
                        obj = obj.replace(placeholder, secret_value)
                return obj
            else:
                return obj

        return replace_placeholders(config_data)

    def load_yaml_config(self) -> Dict[str, Any]:
        """Load YAML configuration file"""
        if not self.yaml_file.exists():
            logger.warning(f"YAML config file not found: {self.yaml_file}")
            logger.info("Using default configuration")
            return {}

        try:
            with open(self.yaml_file, "r") as f:
                config_data = yaml.safe_load(f) or {}

            logger.info(f"Loaded YAML configuration from {self.yaml_file}")
            return config_data

        except Exception as e:
            logger.error(f"Failed to load YAML config from {self.yaml_file}: {e}")
            return {}

    def load_config(self) -> Settings:
        """Load complete configuration with secrets interpolation"""
        logger.info("Loading Entity configuration...")

        # Load secrets first
        secrets = self.load_secrets()

        # Load YAML configuration
        config_data = self.load_yaml_config()

        # Interpolate secrets into configuration
        config_data = self.interpolate_secrets(config_data, secrets)

        # Create Settings object
        settings = Settings(config_data)

        logger.info(f"Configuration loaded successfully:")
        logger.info(f"  Entity: {settings.entity.name} ({settings.entity.entity_id})")
        logger.info(
            f"  Database: {settings.database.host}:{settings.database.port}/{settings.database.name}"
        )
        logger.info(f"  Ollama: {settings.ollama.base_url} ({settings.ollama.model})")
        logger.info(f"  Debug: {settings.debug}")

        return settings


# Global config loader instance
_config_loader = ConfigLoader()


def load_settings(config_path: str = None) -> Settings:
    """Load settings from YAML configuration with INI secrets"""
    return _config_loader.load_config()


def get_settings() -> Settings:
    """Get current settings (loads if not already loaded)"""
    return _config_loader.load_config()


def get_settings_dependency() -> Settings:
    """FastAPI dependency for getting settings"""
    return get_settings()


def reload_config() -> Settings:
    """Force reload configuration from files"""
    global _config_loader
    _config_loader = ConfigLoader()
    return _config_loader.load_config()
