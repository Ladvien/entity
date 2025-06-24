# src/plugins/prompts/manager.py

import os
import importlib.util
from pathlib import Path
from typing import Dict, List, Type, Optional
import logging

from src.plugins.prompts.plugin import PromptPlugin


logger = logging.getLogger(__name__)


class PromptPluginManager:
    """Clean prompt plugin manager - no legacy support"""

    def __init__(self):
        self.plugins: Dict[str, Type[PromptPlugin]] = {}
        self.loaded_instances: Dict[str, PromptPlugin] = {}

    def load_plugin(self, plugin_name: str) -> PromptPlugin:
        """Load a plugin instance by name"""
        if plugin_name not in self.plugins:
            available = list(self.plugins.keys())
            raise ValueError(
                f"Plugin '{plugin_name}' not found. Available: {available}"
            )

        # Return cached instance if available
        if plugin_name in self.loaded_instances:
            return self.loaded_instances[plugin_name]

        # Create new instance
        plugin_class = self.plugins[plugin_name]
        plugin_instance = plugin_class()

        # Cache the instance
        self.loaded_instances[plugin_name] = plugin_instance

        logger.debug(f"Loaded plugin instance: {plugin_name}")
        return plugin_instance

    def list_available_plugins(self) -> List[str]:
        """Get list of available plugin names"""
        return list(self.plugins.keys())

    def validate_plugin(self, plugin: PromptPlugin) -> bool:
        """Validate a plugin instance"""
        try:
            validation_result = plugin.validate_prompt()
            return validation_result.is_valid
        except Exception as e:
            logger.error(f"Plugin validation failed: {e}")
            return False

    def auto_discover_plugins(self, plugin_dir: str) -> List[str]:
        """Automatically discover and register plugins from a directory"""
        discovered = []
        plugin_path = Path(plugin_dir)

        if not plugin_path.exists():
            logger.warning(f"Plugin directory not found: {plugin_dir}")
            return discovered

        # Look for Python files in the plugin directory
        for file_path in plugin_path.glob("*.py"):
            if file_path.name.startswith("__"):
                continue  # Skip __init__.py, __pycache__, etc.

            try:
                plugin_name = file_path.stem
                plugin_class = self._load_plugin_from_file(file_path)

                if plugin_class:
                    self.plugins[plugin_name] = plugin_class
                    discovered.append(plugin_name)
                    logger.info(f"Discovered plugin: {plugin_name}")

            except Exception as e:
                logger.error(f"Failed to load plugin from {file_path}: {e}")

        return discovered

    def _load_plugin_from_file(self, file_path: Path) -> Optional[Type[PromptPlugin]]:
        """Load a plugin class from a Python file"""
        try:
            spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
            if not spec or not spec.loader:
                return None

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find PromptPlugin subclasses in the module
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, PromptPlugin)
                    and attr != PromptPlugin
                ):
                    return attr

            logger.warning(f"No PromptPlugin subclass found in {file_path}")
            return None

        except Exception as e:
            logger.error(f"Error loading plugin from {file_path}: {e}")
            return None

    def register_plugin(self, name: str, plugin_class: Type[PromptPlugin]):
        """Manually register a plugin class"""
        if not issubclass(plugin_class, PromptPlugin):
            raise ValueError(f"Plugin class must inherit from PromptPlugin")

        self.plugins[name] = plugin_class
        logger.info(f"Registered plugin: {name}")

    def get_plugin(self, name: str, config: Dict = None) -> PromptPlugin:
        """Get a plugin instance by name with optional config"""
        if name not in self.plugins:
            available = list(self.plugins.keys())
            raise ValueError(f"Plugin '{name}' not found. Available: {available}")

        # Create new instance with config if provided
        if config is not None:
            plugin_class = self.plugins[name]
            return plugin_class(config)

        # Otherwise use cached/default instance
        return self.load_plugin(name)
