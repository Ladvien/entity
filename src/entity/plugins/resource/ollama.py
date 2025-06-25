# src/entity/plugins/resource/ollama.py
from langchain_community.llms import Ollama
from .base import ResourcePlugin


class OllamaResourcePlugin(ResourcePlugin):
    def get_resource_name(self) -> str:
        return "llm"

    async def initialize(self, config: dict):
        return Ollama(model=config.get("model", "llama3"))
