from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, List

from registry import PluginRegistry

from .manager import PipelineManager


async def _restart_plugin(plugin, new_config: Dict) -> None:
    shutdown = getattr(plugin, "shutdown", None)
    if callable(shutdown):
        await shutdown()
    plugin.config = new_config
    initialize = getattr(plugin, "initialize", None)
    if callable(initialize):
        await initialize()
    if hasattr(plugin, "_config_history"):
        plugin._config_history.append(new_config.copy())
        plugin.config_version += 1


@dataclass
class ConfigUpdateResult:
    success: bool
    error_message: str | None = None
    requires_restart: bool = False
    updated_plugins: List[str] = field(default_factory=list)

    @classmethod
    def success_result(
        cls, updated_plugins: List[str] | None = None
    ) -> "ConfigUpdateResult":
        return cls(True, updated_plugins=updated_plugins or [])

    @classmethod
    def failure_result(cls, msg: str) -> "ConfigUpdateResult":
        return cls(False, error_message=msg)

    @classmethod
    def restart_required(cls, msg: str) -> "ConfigUpdateResult":
        return cls(False, error_message=msg, requires_restart=True)


async def wait_for_pipeline_completion(
    pipeline_manager: PipelineManager | None = None, timeout_seconds: int = 30
):
    start = time.time()
    if pipeline_manager is None:
        return
    while await pipeline_manager.has_active_pipelines_async():
        if time.time() - start > timeout_seconds:
            raise TimeoutError("Timeout waiting for pipelines to complete")
        await asyncio.sleep(0.1)


async def update_plugin_configuration(
    plugin_registry: PluginRegistry,
    plugin_name: str,
    new_config: Dict,
    pipeline_manager: PipelineManager | None = None,
) -> ConfigUpdateResult:
    await wait_for_pipeline_completion(pipeline_manager)
    plugin_instance = plugin_registry.get_plugin(plugin_name)
    if not plugin_instance:
        return ConfigUpdateResult.failure_result(f"Plugin {plugin_name} not found")

    validation_result = plugin_instance.validate_config(new_config)
    if not validation_result.success:
        return ConfigUpdateResult.failure_result(
            f"Validation failed: {validation_result.error_message}"
        )

    dep_check = plugin_instance.validate_dependencies(plugin_registry)
    if not dep_check.success:
        return ConfigUpdateResult.failure_result(
            f"Dependency validation failed: {dep_check.error_message}"
        )

    old_config = getattr(plugin_instance, "config", {})
    old_version = getattr(plugin_instance, "config_version", 1)
    reconfig_result = await plugin_instance.reconfigure(new_config)
    if not reconfig_result.success:
        if reconfig_result.requires_restart:
            try:
                await _restart_plugin(plugin_instance, new_config)
            except Exception as exc:  # noqa: BLE001
                await plugin_instance.rollback_config(old_version)
                return ConfigUpdateResult.failure_result(str(exc))
        else:
            return ConfigUpdateResult.failure_result(
                reconfig_result.error_message or ""
            )

    updated = [plugin_name]

    for dependent in plugin_registry.get_dependents(plugin_name):
        try:
            dep_val = dependent.validate_dependencies(plugin_registry)
            if not dep_val.success:
                raise RuntimeError(
                    dep_val.error_message or "dependency validation failed"
                )
            handled = await dependent.on_dependency_reconfigured(
                plugin_name, old_config, new_config
            )
            if not handled:
                plugin_name_str = plugin_registry.get_plugin_name(dependent)
                raise RuntimeError(
                    f"Dependency cascade failed for plugin: {plugin_name_str}"
                )
            updated.append(plugin_registry.get_plugin_name(dependent))
        except Exception as e:
            await plugin_instance.rollback_config(old_version)
            return ConfigUpdateResult.failure_result(str(e))

    return ConfigUpdateResult.success_result(updated)
