"""
Simplified configuration system - Phase 1 Implementation
Reduces from 10+ config classes to 4 main classes
"""

from typing import Dict, Any, List, Literal, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field, model_validator
import yaml
import os
import re
from pathlib import Path


class DatabaseConfig(BaseModel):
    """Unified data storage configuration"""

    host: str = "localhost"
    port: int = 5432
    name: str = "memory"
    username: str = "postgres"
    password: str = "password"

    db_schema: str = "entity"
    history_table: str = "chat_history"

    min_pool_size: int = 2
    max_pool_size: int = 10

    init_on_startup: bool = True


class AdapterConfig(BaseModel):
    """Unified adapter configuration with type discrimination"""

    type: Literal["tts", "webhook", "translation", "audio"]
    enabled: bool = True
    settings: Dict[str, Any] = Field(default_factory=dict)


class TTSConfig(BaseModel):
    """TTS configuration with audio settings included"""

    base_url: str = "http://localhost:8888"
    voice_name: str = "bf_emma"
    voice_sample_path: str = "voice_samples/ai_mee.wav"
    output_format: str = "wav"
    speed: float = 0.3
    cfg_weight: float = 0.9
    exaggeration: float = 0.5

    sample_rates: List[int] = Field(
        default_factory=lambda: [44100, 48000, 22050, 16000, 8000]
    )
    fade_out_samples: int = 2000


class OllamaConfig(BaseModel):
    base_url: str = "http://localhost:11434"
    model: str = "llama3.1:8b-instruct"
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1


class MemoryConfig(BaseModel):
    collection_name: str = "entity_memory"
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    max_context_length: int = 1000
    similarity_threshold: float = 0.3
    memory_limit: int = 50
    pruning_enabled: bool = True
    pruning_days: int = 90
    keep_important_threshold: float = 0.7
    min_access_count: int = 2


class PromptConfig(BaseModel):
    plugin: str = None
    template: Optional[str] = None  # Template name  # noqa: F821

    # Strategy-specific settings
    strategy_settings: Dict[str, Any] = Field(default_factory=dict)

    variables: List[str] = Field(default_factory=list)
    base_prompt: str = ""


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    log_level: str = "info"


class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_enabled: bool = False
    file_path: str = "logs/entity.log"
    max_file_size: int = 10485760
    backup_count: int = 5


class ToolConfig(BaseModel):
    plugin_path: str = "./plugins_user/plugins"
    max_total_tool_uses: int = 10

    class EnabledTool(BaseModel):
        name: str
        max_uses: int

    enabled: List[EnabledTool] = Field(default_factory=list)


class EntityConfig(BaseModel):
    """Agent configuration with integrated personality"""

    entity_id: str = "jade"
    max_iterations: int = 6

    name: str = "Jade"
    sarcasm_level: float = 0.8
    loyalty_level: float = 0.6
    anger_level: float = 0.7
    wit_level: float = 0.9
    response_brevity: float = 0.7
    memory_influence: float = 0.8

    prompt: PromptConfig = Field(default_factory=PromptConfig)


class EntityServerConfig(BaseModel):
    """Main configuration class - simplified structure"""

    config_version: str = "2.0"
    debug: bool = False

    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    tts: TTSConfig = Field(default_factory=TTSConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    entity: EntityConfig = Field(default_factory=EntityConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    tools: ToolConfig = Field(default_factory=ToolConfig)
    adapters: List[AdapterConfig] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_adapters(self) -> "EntityServerConfig":
        if self.adapters and not any(adapter.enabled for adapter in self.adapters):
            raise ValueError("At least one adapter must be enabled")
        return self

    @property
    def database_config(self) -> DatabaseConfig:
        """Backward compatibility"""
        return self.database

    @property
    def personality(self) -> Dict[str, float]:
        """Easy access to personality settings"""
        return {
            "sarcasm_level": self.entity.sarcasm_level,
            "loyalty_level": self.entity.loyalty_level,
            "anger_level": self.entity.anger_level,
            "wit_level": self.entity.wit_level,
            "response_brevity": self.entity.response_brevity,
            "memory_influence": self.entity.memory_influence,
        }

    @property
    def audio_settings(self) -> Dict[str, Any]:
        """Easy access to audio settings from TTS config"""
        return {
            "sample_rates": self.tts.sample_rates,
            "fade_out_samples": self.tts.fade_out_samples,
        }

    @classmethod
    def config_from_file(cls, path: str = "config/config.yml") -> "EntityServerConfig":
        """Load configuration from a YAML file (with .env interpolation)."""
        config_path = Path(os.path.expanduser(path))
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        # Load .env from same dir or root
        env_file = config_path.parent / ".env"
        if not env_file.exists():
            env_file = Path(".env")
        if env_file.exists():
            load_dotenv(env_file)

        with config_path.open() as f:
            raw_config = yaml.safe_load(f)

        return cls._parse_config(raw_config)

    @classmethod
    def config_from_str(cls, yaml_str: str) -> "EntityServerConfig":
        """Load configuration from a YAML string."""
        raw_config = yaml.safe_load(yaml_str)
        return cls._parse_config(raw_config)

    @classmethod
    def _parse_config(cls, raw: dict) -> "EntityServerConfig":
        """Handles optional `data` wrapping and applies env interpolation."""
        # Don't assume data wrapping - use the raw config directly
        config_data = walk_and_replace(raw)
        return cls(**config_data)


VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")


def interpolate_env(value: Any) -> Any:
    """Replace ${VAR_NAME} with environment variable values"""
    if isinstance(value, str):

        def replacer(match):
            var_name = match.group(1)
            return os.getenv(var_name, match.group(0))

        return VAR_PATTERN.sub(replacer, value)
    return value


def walk_and_replace(obj: Any) -> Any:
    """Recursively replace environment variables in nested structures"""
    if isinstance(obj, dict):
        return {k: walk_and_replace(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [walk_and_replace(item) for item in obj]
    else:
        return interpolate_env(obj)
