from pathlib import Path

from .base import BaseInfrastructure


class LocalStorageInfrastructure(BaseInfrastructure):
    """Layer 1 infrastructure for storing files on the local filesystem."""

    def __init__(self, base_path: str, version: str | None = None) -> None:
        """Create the infrastructure rooted at ``base_path``."""

        super().__init__(version)
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True, mode=0o755)

    def resolve_path(self, key: str) -> Path:
        """Return the absolute path for the given storage key."""

        return self.base_path / key

    def health_check(self) -> bool:
        """Return ``True`` if the base path is writable."""
        try:
            test_file = self.base_path / ".health_check"
            test_file.write_text("ok")
            test_file.unlink()
            self.logger.debug("Health check succeeded for %s", self.base_path)
            return True
        except Exception as exc:
            self.logger.warning("Health check failed for %s: %s", self.base_path, exc)
            return False

    async def startup(self) -> None:
        await super().startup()
        self.logger.info("Storage path %s ready", self.base_path)

    async def shutdown(self) -> None:
        await super().shutdown()
