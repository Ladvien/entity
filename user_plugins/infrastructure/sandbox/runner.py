from __future__ import annotations

import subprocess
import tomllib
from pathlib import Path
from typing import Any, Dict

from infrastructure import DockerInfrastructure


class DockerSandboxRunner:
    """Run plugins inside isolated Docker containers."""

    def __init__(self, infrastructure: DockerInfrastructure | None = None) -> None:
        if infrastructure is not None:
            self.infra = infrastructure
        else:
            if DockerInfrastructure is None:
                raise ImportError(
                    "Docker infrastructure is unavailable. Install the 'docker' package."
                )
            self.infra = DockerInfrastructure()

    def _verify_signature(self, plugin_dir: Path) -> None:
        """Verify plugin GPG signature."""
        manifest = plugin_dir / "plugin.toml"
        sig = plugin_dir / "plugin.toml.sig"
        if not sig.exists():
            raise RuntimeError(f"Signature file missing: {sig}")
        result = subprocess.run(
            ["gpg", "--verify", str(sig), str(manifest)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Invalid plugin signature: {result.stderr}")

    def _load_manifest(self, plugin_dir: Path) -> Dict[str, Any]:
        data = (plugin_dir / "plugin.toml").read_text()
        return tomllib.loads(data)

    def run_plugin(self, plugin_dir: str) -> None:
        """Execute plugin in a Docker container with limits."""
        path = Path(plugin_dir)
        self._verify_signature(path)
        manifest = self._load_manifest(path)
        cpu = float(manifest.get("cpu", 1))
        memory = manifest.get("memory", "512m")
        command = ["python", "-m", manifest.get("entrypoint", "main")]
        volumes = {str(path): {"bind": "/plugin", "mode": "ro"}}
        self.infra.run_container(
            self.infra.base_image,
            command,
            cpu=cpu,
            memory=memory,
            volumes=volumes,
        )
