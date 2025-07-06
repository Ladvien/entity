from __future__ import annotations

"""Default configuration values and helpers."""

import os
from typing import Any, Dict, Optional

import httpx

DEFAULT_LOGGING_CONFIG: Dict[str, Any] = {
    "type": "plugins.builtin.adapters.logging:LoggingAdapter",
    "stages": ["deliver"],
}

DEFAULT_LLM_CONFIG: Dict[str, Any] = {
    "type": "pipeline.resources.llm.unified:UnifiedLLMResource",
    "provider": "echo",
}

DEFAULT_RESOURCES: Dict[str, Dict[str, Any]] = {
    "llm": DEFAULT_LLM_CONFIG,
    "memory": {
        "type": "pipeline.resources.memory_resource:MemoryResource",
        "database": {
            "type": "pipeline.resources.duckdb_database:DuckDBDatabaseResource"
        },
        "vector_store": {
            "type": "plugins.builtin.resources.duckdb_vector_store:DuckDBVectorStore"
        },
    },
    "storage": {
        "type": "pipeline.resources.storage_resource:StorageResource",
        "filesystem": {
            "type": "plugins.builtin.resources.local_filesystem:LocalFileSystemResource"
        },
    },
    "cache": {
        "type": "user_plugins.resources.cache:CacheResource",
        "backend": {"type": "pipeline.cache.memory:InMemoryCache"},
    },
}

DEFAULT_TOOLS: Dict[str, Dict[str, Any]] = {
    "search": {"type": "user_plugins.tools.search_tool:SearchTool"},
    "calculator": {"type": "user_plugins.tools.calculator_tool:CalculatorTool"},
}

DEFAULT_ADAPTERS: Dict[str, Dict[str, Any]] = {
    "http": {
        "type": "plugins.builtin.adapters.http:HTTPAdapter",
        "stages": ["parse", "deliver"],
    },
    "websocket": {
        "type": "plugins.builtin.adapters.websocket:WebSocketAdapter",
        "stages": ["deliver"],
    },
    "cli": {"type": "plugins.builtin.adapters.cli:CLIAdapter", "stages": ["deliver"]},
    "logging": DEFAULT_LOGGING_CONFIG,
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
