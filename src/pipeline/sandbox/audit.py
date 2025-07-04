from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Iterable, List


class PluginAuditor:
    """Validate plugin permission manifests."""

    def __init__(self, allowed_resources: Iterable[str] | None = None) -> None:
        self.allowed_resources = set(allowed_resources or [])

    def audit(self, plugin_dir: str) -> List[str]:
        """Return list of disallowed resources."""
        manifest_path = Path(plugin_dir) / "plugin.toml"
        manifest = tomllib.loads(manifest_path.read_text())
        requested = set(manifest.get("resources", []))
        return sorted(requested - self.allowed_resources)
