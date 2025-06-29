from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, List

from .manager import PipelineManager
from .registries import PluginRegistry


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
    plugin_instance = next(
        (
            p
            for p in plugin_registry.list_plugins()
            if getattr(p, "name", p.__class__.__name__) == plugin_name
        ),
        None,
    )
    if not plugin_instance:
        return ConfigUpdateResult.failure_result(f"Plugin {plugin_name} not found")

    validation_result = plugin_instance.validate_config(new_config)
    if not validation_result.success:
        return ConfigUpdateResult.failure_result(
            f"Validation failed: {validation_result.error_message}"
        )

    old_config = getattr(plugin_instance, "config", {})
    reconfig_result = await plugin_instance.reconfigure(new_config)
    if not reconfig_result.success:
        if reconfig_result.requires_restart:
            return ConfigUpdateResult.restart_required(
                reconfig_result.error_message or ""
            )
        return ConfigUpdateResult.failure_result(reconfig_result.error_message or "")

    updated = [plugin_name]

    for dependent in plugin_registry.get_dependents(plugin_name):
        try:
            handled = await dependent.on_dependency_reconfigured(
                plugin_name, old_config, new_config
            )
            if not handled:
                plugin_name_str = getattr(
                    dependent, "name", dependent.__class__.__name__
                )
                msg = f"Dependency cascade failed for plugin: {plugin_name_str}"
                return ConfigUpdateResult.failure_result(msg)
            updated.append(plugin_registry.get_plugin_name(dependent))
        except Exception as e:
            return ConfigUpdateResult.failure_result(str(e))

    return ConfigUpdateResult.success_result(updated)
