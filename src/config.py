# entity/config_models.py

from typing import List, Dict, Optional
from pydantic import BaseModel, Field
import os
import yaml
import re
from typing import Any, Union, Optional
from dotenv import load_dotenv
from rich import print


class DatabaseConfig(BaseModel):
    host: str = "localhost"
    port: int = 5432
    name: str = "memory"
    username: str = "memory"
    password: str = "password"
    min_pool_size: int = 2
    max_pool_size: int = 10


class OllamaConfig(BaseModel):
    base_url: str = "http://localhost:11434"
    model: str = "neural-chat:7b"
    timeout: int = 60
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1


class TTSConfig(BaseModel):
    base_url: str = "http://localhost:8888"
    voice_name: str = "emma"
    voice_sample_path: str = "voice_samples/ai_mee.wav"
    output_format: str = "wav"
    speed: float = 0.3
    cfg_weight: float = 0.9
    exaggeration: float = 0.5


class AudioConfig(BaseModel):
    sample_rates: List[int] = [44100, 48000, 22050, 16000, 8000]
    fade_out_samples: int = 2000


class MemoryConfig(BaseModel):
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    max_context_length: int = 1000
    similarity_threshold: float = 0.3
    memory_limit: int = 5
    pruning_enabled: bool = True
    pruning_days: int = 90
    keep_important_threshold: float = 0.7
    min_access_count: int = 2


class EntityBehaviorConfig(BaseModel):
    entity_id: str = "jade"
    name: str = "Jade"
    sarcasm_level: float = 0.8
    loyalty_level: float = 0.6
    anger_level: float = 0.7
    wit_level: float = 0.9
    response_brevity: float = 0.7
    memory_influence: float = 0.8


class PromptsConfig(BaseModel):
    base_prompt: str
    memory_context_template: str
    personality_modifiers: Dict[str, str] = Field(default_factory=dict)


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


class EntitySystemConfig(BaseModel):
    config_version: str = "2.0"
    debug: bool = False
    database: DatabaseConfig
    ollama: OllamaConfig
    tts: TTSConfig
    audio: AudioConfig
    memory: MemoryConfig
    entity: EntityBehaviorConfig
    prompts: PromptsConfig
    server: ServerConfig
    logging: LoggingConfig


VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")


def interpolate_env(value: Any) -> Any:
    if isinstance(value, str):
        match = VAR_PATTERN.fullmatch(value.strip())
        if match:
            var_name = match.group(1)
            return os.getenv(var_name, value)
    return value


def walk_and_replace(obj: Union[dict, list, str, int, float]) -> Any:
    if isinstance(obj, dict):
        return {k: walk_and_replace(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [walk_and_replace(item) for item in obj]
    else:
        return interpolate_env(obj)


class ConfigLoader:
    def __init__(self, yaml_path: str = "config.yaml", secrets_path: str = ".env"):
        self.yaml_path = yaml_path
        self.secrets_path = secrets_path

    def load(self) -> EntitySystemConfig:
        # Load environment variables
        load_dotenv(self.secrets_path)

        # Load YAML config
        with open(self.yaml_path, "r") as f:
            config_raw = yaml.safe_load(f)

        # Focus on top-level `entity:` section
        if "entity" in config_raw:
            config_raw = config_raw["entity"]

        # Recursively replace ${VAR_NAME} with values from environment
        resolved_config = walk_and_replace(config_raw)

        # Parse into typed config
        config = EntitySystemConfig(**resolved_config)
        print(config)
        return config
