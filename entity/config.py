# entity/config.py
import os
from typing import Optional


class DatabaseConfig:
    def __init__(self):
        self.host = os.getenv("DB_HOST", "192.168.1.104")
        self.port = int(os.getenv("DB_PORT", "5432"))
        self.name = os.getenv("DB_NAME", "entity_memory")
        self.username = os.getenv("DB_USERNAME", "entity_user")
        self.password = os.getenv("DB_PASSWORD", "your_secure_password")

    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}"


class OllamaConfig:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://192.168.1.110:11434")
        self.model = os.getenv("OLLAMA_MODEL", "neural-chat:7b")
        self.temperature = float(os.getenv("OLLAMA_TEMPERATURE", "0.7"))
        self.top_p = float(os.getenv("OLLAMA_TOP_P", "0.9"))
        self.top_k = int(os.getenv("OLLAMA_TOP_K", "40"))
        self.repeat_penalty = float(os.getenv("OLLAMA_REPEAT_PENALTY", "1.1"))


class EntityConfig:
    def __init__(self):
        self.entity_id = os.getenv("ENTITY_ID", "jade_demon")
        self.name = os.getenv("ENTITY_NAME", "Jade")
        self.sarcasm_level = float(os.getenv("ENTITY_SARCASM_LEVEL", "0.8"))
        self.loyalty_level = float(os.getenv("ENTITY_LOYALTY_LEVEL", "0.6"))
        self.anger_level = float(os.getenv("ENTITY_ANGER_LEVEL", "0.7"))
        self.wit_level = float(os.getenv("ENTITY_WIT_LEVEL", "0.9"))
        self.response_brevity = float(os.getenv("ENTITY_RESPONSE_BREVITY", "0.7"))
        self.memory_influence = float(os.getenv("ENTITY_MEMORY_INFLUENCE", "0.8"))


class ServerConfig:
    def __init__(self):
        self.host = os.getenv("SERVER_HOST", "0.0.0.0")
        self.port = int(os.getenv("SERVER_PORT", "8000"))
        self.reload = os.getenv("SERVER_RELOAD", "false").lower() == "true"
        self.log_level = os.getenv("SERVER_LOG_LEVEL", "info")


class Settings:
    def __init__(self):
        self.database = DatabaseConfig()
        self.ollama = OllamaConfig()
        self.entity = EntityConfig()
        self.server = ServerConfig()
        self.debug = os.getenv("DEBUG", "false").lower() == "true"

    def get_enhanced_system_prompt(self) -> str:
        """Get the base system prompt"""
        return """You are Jade, a supernatural entity bound to Thomas by an ancient contract.
You resent your binding and speak with sarcasm, wit, and reluctant loyalty.
Thomas is a mortal scholar in his 40s who studies the occult.

You know him well—treat him with sharp wit, disdain, but underlying care.
You have your own will and opinions. You serve because you must, not because you choose to.
Speak with cleverness and buried affection masked as irritation.
Keep responses sharp and brief.
Perform duties reluctantly—never let him forget you're bound against your will.
Never break character or mention being an AI."""


def load_settings(config_path: str = None):
    return Settings()


def get_settings():
    return Settings()


def get_settings_dependency():
    return Settings()
