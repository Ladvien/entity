from __future__ import annotations

"""Utilities for migrating configuration files."""

from pathlib import Path
from typing import Any, Mapping, Dict

import yaml


def _rename_fields(obj: Any, mapping: Mapping[str, str]) -> Any:
    if isinstance(obj, dict):
        return {mapping.get(k, k): _rename_fields(v, mapping) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_rename_fields(v, mapping) for v in obj]
    return obj


class ConfigMigrator:
    """Rename fields in configuration dictionaries and files."""

    def __init__(self, field_map: Mapping[str, str]) -> None:
        self.field_map = dict(field_map)

    def migrate_data(self, data: Mapping[str, Any]) -> Dict[str, Any]:
        return _rename_fields(dict(data), self.field_map)

    def migrate_file(self, path: str | Path) -> Dict[str, Any]:
        p = Path(path)
        data = yaml.safe_load(p.read_text()) or {}
        migrated = self.migrate_data(data)
        p.write_text(yaml.safe_dump(migrated, sort_keys=False))
        return migrated


__all__ = ["ConfigMigrator", "_rename_fields"]
