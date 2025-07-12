from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from entity.core.plugins import ValidationResult
from entity.core.registries import PluginRegistry


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

    stages = new_config.get("stages")
    if stages is not None and stages != getattr(plugin, "stages", None):
        return ConfigUpdateResult(
            False,
            True,
            "Topology changes require restart",
        )
    deps = new_config.get("dependencies")
    if deps is not None and deps != getattr(plugin, "dependencies", None):
        return ConfigUpdateResult(
            False,
            True,
            "Topology changes require restart",
        )

    validator = getattr(plugin.__class__, "validate_config", None)
    if callable(validator):
        result = validator(new_config)
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
        plugin.config = old_config
        plugin._config_history.pop()
        plugin.config_version -= 1
        return ConfigUpdateResult(False, False, f"Failed to update: {exc}")
