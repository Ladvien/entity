from pathlib import Path


class LocalStorageInfrastructure:
    """Layer 1 infrastructure for storing files on the local filesystem."""

    def __init__(self, base_path: str) -> None:
        """Create the infrastructure rooted at ``base_path``."""

        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def resolve_path(self, key: str) -> Path:
        """Return the absolute path for the given storage key."""

        return self.base_path / key
