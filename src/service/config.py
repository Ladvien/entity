# entity_service/config.py
"""
Unified configuration system matching your exact YAML structure
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import yaml
import os
import re
from pathlib import Path


class ToolConfig(BaseModel):
    enabled: List[str] = []


# Database Configuration
class DatabaseConfig(BaseModel):
    host: str = "localhost"
    port: int = 5432
    name: str = "memory"
    username: str = "postgres"
    password: str = "password"
    min_pool_size: int = 2
    max_pool_size: int = 10


# Ollama Configuration
class OllamaConfig(BaseModel):
    base_url: str = "http://localhost:11434"
    model: str = "llama3.1:8b-instruct-q6_K"
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1


# TTS Configuration
class TTSConfig(BaseModel):
    base_url: str = "http://localhost:8888"
    voice_name: str = "bf_emma"
    voice_sample_path: str = "voice_samples/ai_mee.wav"
    output_format: str = "wav"
    speed: float = 0.3
    cfg_weight: float = 0.9
    exaggeration: float = 0.5


# Audio Configuration
class AudioConfig(BaseModel):
    sample_rates: List[int] = [44100, 48000, 22050, 16000, 8000]
    fade_out_samples: int = 2000


# Memory Configuration
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


class PersonalityConfig(BaseModel):
    name: str = "Jade"
    sarcasm_level: float = 0.8
    loyalty_level: float = 0.6
    anger_level: float = 0.7
    wit_level: float = 0.9
    response_brevity: float = 0.7
    memory_influence: float = 0.8
    base_prompt: Optional[str] = None
    traits: Optional[str] = "sarcastic and impatient"


class EntityConfig(BaseModel):
    entity_id: str = "jade"
    max_iterations: int = 50
    personality: PersonalityConfig = PersonalityConfig()


# Prompts Configuration
class PromptsConfig(BaseModel):
    memory_context_template: str = """
--- Relevant Memories ---
{memories}
--- End Memories ---
"""
    personality_modifiers: Dict[str, str] = Field(default_factory=dict)
    sarcastic_suffixes: List[str] = Field(default_factory=list)
    angry_suffixes: List[str] = Field(default_factory=list)
    neutral_suffixes: List[str] = Field(default_factory=list)


# Server Configuration
class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    log_level: str = "info"


# Logging Configuration
class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_enabled: bool = False
    file_path: str = "logs/entity.log"
    max_file_size: int = 10485760
    backup_count: int = 5


# Main Unified Configuration
class UnifiedConfig(BaseModel):
    """Main configuration class matching your exact YAML structure"""

    config_version: str = "2.0"
    debug: bool = False
    database: DatabaseConfig
    ollama: OllamaConfig
    tts: TTSConfig
    audio: AudioConfig
    memory: MemoryConfig
    entity: EntityConfig
    prompts: PromptsConfig
    server: ServerConfig
    storage: "StorageConfig"
    logging: LoggingConfig
    tools: ToolConfig

    class Config:
        # Allow use of both attribute and dictionary access
        extra = "forbid"  # Fail if unknown fields are present


class StorageConfig(BaseModel):
    backend: str = "postgres"
    history_table: str = "chat_history"
    init_on_startup: bool = True


# Environment variable interpolation
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


def load_config(config_path: str = "config.yaml") -> UnifiedConfig:
    """Load configuration from YAML file with environment variable substitution"""
    # Expand path
    config_path = os.path.expanduser(config_path)
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    # Load environment variables from .env if it exists
    env_file = config_path.parent / ".env"
    if env_file.exists():
        from dotenv import load_dotenv

        load_dotenv(env_file)

    # Load YAML
    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)

    # Replace environment variables
    config_data = walk_and_replace(raw_config)

    # Parse and validate
    try:
        config = UnifiedConfig(**config_data)
        return config
    except Exception as e:
        print(f"Configuration validation error: {e}")
        raise
