from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from entity.core.plugins import ValidationResult
from entity.core.registries import PluginRegistry
from entity.core.plugins.utils import validate_reconfiguration_params
from entity.utils.logging import get_logger


logger = get_logger(__name__)


@dataclass
class ConfigUpdateResult:
    success: bool
    requires_restart: bool = False
    error_message: str = ""


async def update_plugin_configuration(
    registry: PluginRegistry,
    name: str,
    new_config: dict[str, Any],
    *,
    pipeline_manager: Any | None = None,
) -> ConfigUpdateResult:
    """Update ``name`` plugin with ``new_config`` if allowed."""

    plugin = registry.get_plugin(name)
    if plugin is None:
        return ConfigUpdateResult(False, True, f"Plugin '{name}' not registered")

    result = validate_reconfiguration_params(plugin.config, new_config)
    if not result.success:
        plugin._config_history.append(plugin.config.copy())
        diff = {
            k: (plugin.config.get(k), new_config.get(k))
            for k in set(plugin.config) | set(new_config)
            if plugin.config.get(k) != new_config.get(k)
        }
        msg = f"{result.message}. Differences: {diff}" if diff else result.message
        return ConfigUpdateResult(False, True, msg)

    unknown_keys = set(new_config) - set(plugin.config)
    if unknown_keys:
        plugin._config_history.append(plugin.config.copy())
        diff = {k: new_config[k] for k in unknown_keys}
        msg = (
            f"Unknown configuration fields: {sorted(unknown_keys)}. Differences: {diff}"
        )
        return ConfigUpdateResult(False, True, msg)

    validator = getattr(plugin.__class__, "validate_config", None)
    if callable(validator):
        result = validator(new_config)
        if asyncio.iscoroutine(result):
            result = await result
        if not isinstance(result, ValidationResult):
            raise TypeError("validate_config must return ValidationResult")
        if not result.success:
            return ConfigUpdateResult(False, False, result.message)

    if not plugin.supports_runtime_reconfiguration():
        return ConfigUpdateResult(
            False,
            True,
            "Plugin does not support runtime reconfiguration",
        )

    if pipeline_manager is not None and hasattr(
        pipeline_manager, "has_active_pipelines_async"
    ):
        while await pipeline_manager.has_active_pipelines_async():
            await asyncio.sleep(0.05)
    else:
        # Minimal safeguard for concurrent pipelines
        await asyncio.sleep(0.2)

    old_config = plugin.config.copy()
    try:
        handler = getattr(plugin, "_handle_reconfiguration", None)
        if asyncio.iscoroutinefunction(handler):
            await handler(old_config, new_config)
        plugin._config_history.append(new_config.copy())
        plugin.config_version += 1
        plugin.config = new_config

        for dep in registry.list_plugins():
            dep_name = registry.get_plugin_name(dep)
            if name in getattr(dep, "dependencies", []):
                cb = getattr(dep, "on_dependency_reconfigured", None)
                if asyncio.iscoroutinefunction(cb):
                    ok = await cb(name, old_config, new_config)
                    if ok is False:
                        raise RuntimeError(
                            f"Dependency '{dep_name}' rejected configuration"
                        )
        return ConfigUpdateResult(True)
    except Exception as exc:  # noqa: BLE001 - report error and rollback
        version = (
            plugin.config_version - 1
            if len(plugin._config_history) > 1
            else plugin.config_version
        )
        try:
            await plugin.rollback_config(version)
        except Exception as rollback_exc:  # noqa: BLE001 - ignore nested error
            logger.exception("Failed to rollback plugin '%s': %s", name, rollback_exc)
        return ConfigUpdateResult(False, False, f"Failed to update: {exc}")


__all__ = ["ConfigUpdateResult", "update_plugin_configuration"]
