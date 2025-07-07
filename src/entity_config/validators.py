"""Shared configuration validation helpers."""

from __future__ import annotations

from typing import Any, Mapping


def _validate_memory(config: Mapping[str, Any]) -> None:
    """Validate nested memory configuration."""
    mem_cfg = config.get("plugins", {}).get("resources", {}).get("memory")
    if not mem_cfg:
        return
    backend = mem_cfg.get("backend")
    if backend is not None and not isinstance(backend, Mapping):
        raise ValueError("memory: 'backend' must be a mapping")
    if isinstance(backend, Mapping) and "type" in backend:
        if not isinstance(backend["type"], str):
            raise ValueError("memory: 'backend.type' must be a string")


def _validate_vector_memory(config: Mapping[str, Any]) -> None:
    """Ensure vector memory configuration contains required fields."""
    vm_cfg = config.get("plugins", {}).get("resources", {}).get("vector_store")
    if not vm_cfg:
        return
    table = vm_cfg.get("table")
    if not isinstance(table, str) or not table:
        raise ValueError("vector_memory: 'table' is required")
    embedding = vm_cfg.get("embedding_model")
    if not isinstance(embedding, Mapping):
        raise ValueError("vector_memory: 'embedding_model' must be a mapping")
    if not embedding.get("name"):
        raise ValueError("vector_memory: 'embedding_model.name' is required")
    if "dimensions" in embedding:
        try:
            int(embedding["dimensions"])
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "vector_memory: 'embedding_model.dimensions' must be an integer"
            ) from exc


def _validate_cache(config: Mapping[str, Any]) -> None:
    """Validate optional cache configuration."""
    cache_cfg = config.get("plugins", {}).get("resources", {}).get("cache")
    if not cache_cfg:
        return
    backend = cache_cfg.get("backend")
    if backend is not None and not isinstance(backend, Mapping):
        raise ValueError("cache: 'backend' must be a mapping")
    if isinstance(backend, Mapping) and "type" in backend:
        if not isinstance(backend["type"], str):
            raise ValueError("cache: 'backend.type' must be a string")


__all__ = ["_validate_memory", "_validate_vector_memory", "_validate_cache"]
