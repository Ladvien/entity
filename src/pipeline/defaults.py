from __future__ import annotations

"""Default configuration values and helpers."""

import os
from typing import Any, Dict, Optional

import httpx

DEFAULT_LOGGING_CONFIG: Dict[str, Any] = {
    "type": "plugins.resources.structured_logging:StructuredLogging",
    "level": "INFO",
    "json": True,
    "file_enabled": False,
}

DEFAULT_LLM_CONFIG: Dict[str, Any] = {
    "type": "pipeline.resources.llm.unified:UnifiedLLMResource",
    "provider": "echo",
}

DEFAULT_RESOURCES: Dict[str, Dict[str, Any]] = {
    "llm": DEFAULT_LLM_CONFIG,
    "memory": {
        "type": "pipeline.resources.memory_resource:MemoryResource",
        "backend": {"type": "pipeline.resources.memory_resource:SimpleMemoryResource"},
    },
    "cache": {
        "type": "pipeline.user_plugins.resources.cache:CacheResource",
        "backend": {"type": "pipeline.cache.memory:InMemoryCache"},
    },
    "logging": DEFAULT_LOGGING_CONFIG,
}

DEFAULT_TOOLS: Dict[str, Dict[str, Any]] = {
    "search": {"type": "pipeline.user_plugins.tools.search_tool:SearchTool"},
    "calculator": {
        "type": "pipeline.user_plugins.tools.calculator_tool:CalculatorTool"
    },
}

DEFAULT_ADAPTERS: Dict[str, Dict[str, Any]] = {
    "http": {"type": "plugins.adapters.http:HTTPAdapter"},
    "websocket": {"type": "plugins.adapters.websocket:WebSocketAdapter"},
    "cli": {"type": "plugins.adapters.cli:CLIAdapter"},
}

DEFAULT_CONFIG: Dict[str, Any] = {
    "plugins": {
        "resources": DEFAULT_RESOURCES,
        "tools": DEFAULT_TOOLS,
        "adapters": DEFAULT_ADAPTERS,
    }
}


def discover_local_llm() -> Optional[Dict[str, Any]]:
    """Return configuration for a local LLM server if available."""
    base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.environ.get("OLLAMA_MODEL")
    try:
        resp = httpx.get(f"{base_url}/api/tags", timeout=1)
        resp.raise_for_status()
        if not model:
            data = resp.json()
            models = data.get("models")
            if models and isinstance(models, list) and models[0].get("name"):
                model = str(models[0]["name"])
    except Exception:  # noqa: BLE001 - best effort discovery
        return None
    if not model:
        model = "tinyllama"
    return {
        "type": "pipeline.resources.llm.unified:UnifiedLLMResource",
        "provider": "ollama",
        "base_url": base_url,
        "model": model,
    }
