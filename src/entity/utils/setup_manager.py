from __future__ import annotations

from pathlib import Path
import duckdb
import httpx


class Layer0SetupManager:
    """Handle zero-config environment checks."""

    def __init__(
        self,
        *,
        db_path: str = "./agent_memory.duckdb",
        files_dir: str = "./agent_files",
        model: str = "llama3",
        base_url: str = "http://localhost:11434",
    ) -> None:
        self.db_path = Path(db_path)
        self.files_dir = Path(files_dir)
        self.model = model
        self.base_url = base_url.rstrip("/")

    async def ensure_ollama(self) -> None:
        """Verify local Ollama installation and model."""
        url = f"{self.base_url}/api/tags"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url)
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                "Ollama not reachable at http://localhost:11434. "
                "Install from https://ollama.com and start the service."
            ) from exc
        tags = resp.json().get("models", [])
        if not tags:
            raise RuntimeError(
                f"No Ollama models installed. Run 'ollama pull {self.model}'."
            )

    def setup_resources(self) -> None:
        """Create local resources if they do not exist."""
        if not self.db_path.exists():
            conn = duckdb.connect(str(self.db_path))
            conn.close()
        self.files_dir.mkdir(parents=True, exist_ok=True)
