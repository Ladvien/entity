from __future__ import annotations

from pathlib import Path
import duckdb
import httpx
from logging import Logger

from .logging import get_logger


logger = get_logger(__name__)


class Layer0SetupManager:
    """Handle zero-config environment checks."""

    def __init__(
        self,
        *,
        db_path: str = "./agent_memory.duckdb",
        files_dir: str = "./agent_files",
        model: str = "llama3",
        base_url: str = "http://localhost:11434",
        logger: Logger | None = None,
    ) -> None:
        self.db_path = Path(db_path)
        self.files_dir = Path(files_dir)
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.logger = logger or get_logger(self.__class__.__name__)

    async def ensure_ollama(self) -> bool:
        """Return ``True`` when Ollama and the desired model are available."""
        url = f"{self.base_url}/api/tags"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=2)
        except Exception:  # noqa: BLE001
            self.logger.warning(
                "Ollama not reachable at %s. Install from https://ollama.com and start the service.",
                self.base_url,
            )
            return False
        tags = resp.json().get("models", [])
        if not tags:
            self.logger.warning(
                "No Ollama models installed. Run 'ollama pull %s'.", self.model
            )
            return False
        names = [m.get("name") for m in tags]
        if self.model not in names:
            self.logger.warning(
                "Model '%s' missing. Run 'ollama pull %s'.", self.model, self.model
            )
            return False
        return True

    def setup_resources(self) -> None:
        """Create local resources if they do not exist."""
        if not self.db_path.exists():
            conn = duckdb.connect(str(self.db_path))
            conn.close()
            self.logger.info("Created DuckDB database at %s", self.db_path)
        self.files_dir.mkdir(parents=True, exist_ok=True)
        if not any(self.files_dir.iterdir()):
            self.logger.info("Created storage directory at %s", self.files_dir)

    async def setup(self) -> None:
        """Ensure local resources and Ollama."""
        self.setup_resources()
        await self.ensure_ollama()
