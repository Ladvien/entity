"""Runtime plugin reconfiguration and helper functions."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, List

from registry import PluginRegistry, SystemRegistries
from pipeline.interfaces import import_plugin_class
from pipeline.stages import PipelineStage

from .manager import PipelineManager


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


def validate_topology(
    registries: SystemRegistries, new_config: Dict
) -> ConfigUpdateResult:
    """Ensure ``new_config`` matches the running plugin topology."""

    plugins_cfg = new_config.get("plugins", {})

    cfg_resources = set(plugins_cfg.get("resources", {}).keys())
    cfg_tools = set(plugins_cfg.get("tools", {}).keys())
    cfg_other: set[str] = set()
    for key in ("adapters", "prompts"):
        cfg_other.update(plugins_cfg.get(key, {}).keys())

    def _get(obj: SystemRegistries | tuple, attr: str, idx: int):
        return getattr(obj, attr, obj[idx])

    resource_reg = _get(registries, "resources", 1)
    tool_reg = _get(registries, "tools", 2)
    plugin_reg = _get(registries, "plugins", 0)

    current_resources = set(getattr(resource_reg, "_resources", {}).keys())
    current_tools = set(getattr(tool_reg, "_tools", {}).keys())
    current_other = {plugin_reg.get_plugin_name(p) for p in plugin_reg.list_plugins()}

    if cfg_resources != current_resources:
        return ConfigUpdateResult.failure_result("Resource changes require restart")
    if cfg_tools != current_tools:
        return ConfigUpdateResult.failure_result("Tool changes require restart")
    if cfg_other != current_other:
        return ConfigUpdateResult.failure_result(
            "Plugin additions or removals require restart"
        )
    return ConfigUpdateResult.success_result()


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

    if "type" in new_config:
        try:
            new_cls = import_plugin_class(str(new_config["type"]))
        except Exception as exc:  # noqa: BLE001
            return ConfigUpdateResult.failure_result(str(exc))
        if new_cls is not plugin_instance.__class__:
            return ConfigUpdateResult.restart_required(
                "Plugin type changes require restart"
            )

    if "stages" in new_config:
        try:
            new_stages = [PipelineStage.ensure(s) for s in new_config["stages"]]
        except Exception as exc:  # noqa: BLE001
            return ConfigUpdateResult.failure_result(str(exc))
        if list(plugin_instance.__class__.stages) != new_stages:
            return ConfigUpdateResult.failure_result(
                "Stage changes require full restart"
            )

    if "dependencies" in new_config:
        current_deps = set(getattr(plugin_instance.__class__, "dependencies", []))
        if current_deps != set(new_config["dependencies"]):
            return ConfigUpdateResult.failure_result(
                "Dependency changes require full restart"
            )

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
            return ConfigUpdateResult.restart_required(
                reconfig_result.error_message
                or "Plugin requires restart for configuration changes"
            )
        return ConfigUpdateResult.failure_result(reconfig_result.error_message or "")

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
