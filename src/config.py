# entity/config_models.py (Updated sections)

from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator
import os
import yaml
import re
from dotenv import load_dotenv
from rich import print


class DatabaseConfig(BaseModel):
    host: str = Field(
        default="localhost",
        description="Database host address",
        min_length=1,
        max_length=255,
    )
    port: int = Field(default=5432, ge=1, le=65535, description="Database port number")
    name: str = Field(
        default="memory",
        description="Database name",
        min_length=1,
        max_length=63,
        pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$",
    )
    username: str = Field(
        default="memory", description="Database username", min_length=1, max_length=63
    )
    password: str = Field(
        default="password", description="Database password", min_length=1
    )
    min_pool_size: int = Field(
        default=2, ge=1, le=50, description="Minimum connection pool size"
    )
    max_pool_size: int = Field(
        default=10, ge=1, le=100, description="Maximum connection pool size"
    )

    # Optional advanced settings
    connection_timeout: int = Field(
        default=30, ge=1, le=300, description="Connection timeout in seconds"
    )
    command_timeout: int = Field(
        default=60, ge=1, le=600, description="Command timeout in seconds"
    )
    ssl_mode: str = Field(
        default="prefer",
        description="SSL connection mode",
        pattern=r"^(disable|allow|prefer|require|verify-ca|verify-full)$",
    )
    ssl_cert_path: Optional[str] = Field(
        default=None, description="Path to SSL certificate file"
    )
    ssl_key_path: Optional[str] = Field(
        default=None, description="Path to SSL key file"
    )
    ssl_ca_path: Optional[str] = Field(default=None, description="Path to SSL CA file")

    @field_validator("host")
    @classmethod
    def validate_host(cls, v):
        """Validate hostname or IP address"""
        if not v or v.isspace():
            raise ValueError("Host cannot be empty or whitespace")

        # Basic hostname validation (allows localhost, IPs, and domain names)
        hostname_pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$"
        ip_pattern = r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"

        if v == "localhost" or re.match(hostname_pattern, v) or re.match(ip_pattern, v):
            return v

        raise ValueError(f"Invalid host format: {v}")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v):
        """Basic password validation"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        # In production, you might want stronger requirements
        if v in ["password", "123456", "admin", "root", "postgres"]:
            raise ValueError("Password is too weak - avoid common passwords")

        return v

    @field_validator("name", "username")
    @classmethod
    def validate_db_identifier(cls, v):
        """Validate database identifiers (name, username)"""
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", v):
            raise ValueError(
                "Must start with letter and contain only letters, numbers, and underscores"
            )
        return v

    @model_validator(mode="after")
    def validate_pool_sizes(self):
        """Ensure pool size configuration is logical"""
        if self.min_pool_size > self.max_pool_size:
            raise ValueError("min_pool_size cannot be greater than max_pool_size")

        if self.max_pool_size > 50:  # Reasonable upper limit
            raise ValueError("max_pool_size should not exceed 50 for most applications")

        return self

    @model_validator(mode="after")
    def validate_ssl_config(self):
        """Validate SSL configuration consistency"""
        # If SSL certificates are provided, SSL mode should be appropriate
        if (
            any([self.ssl_cert_path, self.ssl_key_path, self.ssl_ca_path])
            and self.ssl_mode == "disable"
        ):
            raise ValueError("SSL certificates provided but SSL is disabled")

        # If using verify modes, CA certificate should be provided
        if self.ssl_mode in ["verify-ca", "verify-full"] and not self.ssl_ca_path:
            raise ValueError(f"SSL mode '{self.ssl_mode}' requires ssl_ca_path")

        return self

    @property
    def connection_string(self) -> str:
        """Generate PostgreSQL connection string"""
        base_url = f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}"

        # Add SSL parameters if configured
        params = []
        if self.ssl_mode != "prefer":  # 'prefer' is default, no need to specify
            params.append(f"sslmode={self.ssl_mode}")

        if self.ssl_cert_path:
            params.append(f"sslcert={self.ssl_cert_path}")

        if self.ssl_key_path:
            params.append(f"sslkey={self.ssl_key_path}")

        if self.ssl_ca_path:
            params.append(f"sslrootcert={self.ssl_ca_path}")

        # Add connection timeouts
        params.append(f"connect_timeout={self.connection_timeout}")

        if params:
            base_url += "?" + "&".join(params)

        return base_url

    @property
    def async_connection_string(self) -> str:
        """Generate async PostgreSQL connection string"""
        return self.connection_string.replace("postgresql://", "postgresql+asyncpg://")

    def get_pool_config(self) -> dict:
        """Get connection pool configuration for SQLAlchemy"""
        return {
            "pool_size": self.min_pool_size,
            "max_overflow": self.max_pool_size - self.min_pool_size,
            "pool_timeout": self.connection_timeout,
            "pool_recycle": 3600,  # Recycle connections after 1 hour
            "pool_pre_ping": True,  # Validate connections before use
        }

    def mask_sensitive_data(self) -> dict:
        """Return config dict with sensitive data masked for logging"""
        data = self.model_dump()
        data["password"] = "***"
        return data

    class Config:
        # Allow validation to run even when fields are not provided
        validate_assignment = True
        # Provide examples for documentation
        json_schema_extra = {
            "example": {
                "host": "192.168.1.104",
                "port": 5432,
                "name": "memory_db",
                "username": "jade_user",
                "password": "secure_password_123",
                "min_pool_size": 3,
                "max_pool_size": 15,
                "connection_timeout": 30,
                "ssl_mode": "require",
            }
        }


class OllamaConfig(BaseModel):
    base_url: str = "http://localhost:11434"
    model: str = "neural-chat:7b"
    timeout: int = 60
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1

    def model_dump(self) -> Dict[str, Any]:
        """Convert to dict format expected by LangChain."""
        return {
            "base_url": self.base_url,
            "model": self.model,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "repeat_penalty": self.repeat_penalty,
            "timeout": self.timeout,
        }


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
    # Remove the nested database config since it's already at the top level
    collection_name: str = "entity_memory"
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

        print(f"🔍 Raw YAML structure: {list(config_raw.keys())}")

        # Check if we have a nested entity structure
        if "entity" in config_raw:
            print(
                f"🔍 Found 'entity' key with content: {list(config_raw['entity'].keys())}"
            )

            # Check if entity contains the full config or just entity behavior
            entity_content = config_raw["entity"]
            if "database" in entity_content and "ollama" in entity_content:
                # This is the full config nested under 'entity'
                print("✅ Using full config from 'entity' section")
                resolved_config = entity_content
            else:
                # The 'entity' key only contains entity behavior, use the whole config
                print("✅ Using root level config, 'entity' is just behavior config")
                resolved_config = config_raw
        else:
            print("✅ Using root level config (no 'entity' wrapper)")
            resolved_config = config_raw

        print(f"📋 Final config keys: {list(resolved_config.keys())}")

        # Recursively replace ${VAR_NAME} with values from environment
        resolved_config = walk_and_replace(resolved_config)

        # Parse into typed config
        try:
            config = EntitySystemConfig(**resolved_config)
            print("✅ Configuration loaded successfully")
            return config
        except Exception as e:
            print(f"❌ Configuration validation failed: {e}")

            # Debug information
            expected_keys = set(EntitySystemConfig.model_fields.keys())
            actual_keys = (
                set(resolved_config.keys())
                if isinstance(resolved_config, dict)
                else set()
            )
            missing_keys = expected_keys - actual_keys
            extra_keys = actual_keys - expected_keys

            if missing_keys:
                print(f"🔴 Missing required keys: {missing_keys}")
            if extra_keys:
                print(f"🟡 Extra keys found: {extra_keys}")

            # Show the structure we're trying to parse
            print("🔍 Config structure being parsed:")
            for key, value in resolved_config.items():
                if isinstance(value, dict):
                    print(f"  {key}: {list(value.keys())}")
                else:
                    print(f"  {key}: {type(value).__name__}")
            raise
