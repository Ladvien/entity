"""Utilities for migrating configuration schemas between versions."""

from __future__ import annotations

from typing import Any, Callable, Dict, List


class Migration:
    """Represents a single config migration step."""

    def __init__(
        self, version: int, upgrade: Callable[[Dict[str, Any]], Dict[str, Any]]
    ):
        self.version = version
        self.upgrade = upgrade


class MigrationManager:
    """Apply registered migrations sequentially."""

    def __init__(self) -> None:
        self._migrations: List[Migration] = []

    def register(self, migration: Migration) -> None:
        self._migrations.append(migration)
        self._migrations.sort(key=lambda m: m.version)

    def upgrade(self, data: Dict[str, Any], current: int) -> tuple[Dict[str, Any], int]:
        for m in self._migrations:
            if m.version > current:
                data = m.upgrade(data)
                current = m.version
        return data, current


__all__ = ["Migration", "MigrationManager"]
