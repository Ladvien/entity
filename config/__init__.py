"""Backward compatibility package for configuration helpers."""

from importlib import import_module
from types import ModuleType

from src.config import *  # noqa: F401,F403


def __getattr__(name: str) -> ModuleType:
    return import_module(f"src.config.{name}")
