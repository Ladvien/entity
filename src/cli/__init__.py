"""Compatibility imports for the unified CLI."""

from importlib import import_module


def __getattr__(name: str):
    if name in {"CLI", "main"}:
        module = import_module("entity.cli")
        return module.EntityCLI if name == "CLI" else module.main
    raise AttributeError(name)


__all__ = ["CLI", "main"]
