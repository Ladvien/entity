from __future__ import annotations

from pathlib import Path
import asyncio
import importlib
from logging import Logger
import httpx

try:  # attempt to load duckdb lazily
    duckdb = importlib.import_module("duckdb")
except ModuleNotFoundError:  # pragma: no cover - environment may omit duckdb
    duckdb = None

from .logging import get_logger
from entity.workflows.minimal import minimal_workflow
from entity.workflows import Workflow


logger = get_logger(__name__)


async def pull_model(model: str, *, logger: Logger | None = None) -> bool:
    """Download ``model`` using ``ollama pull``.

    Returns ``True`` if the command completes successfully.
    """
    logger = logger or get_logger("ollama")
    try:
        proc = await asyncio.create_subprocess_exec(
            "ollama",
            "pull",
            model,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError:  # pragma: no cover - runtime dependency missing
        logger.error("Ollama CLI not found. Install from https://ollama.com.")
        return False

    out, err = await proc.communicate()
    if proc.returncode != 0:
        logger.error("Failed to pull %s: %s", model, err.decode() or out.decode())
        return False

    logger.info("Model '%s' downloaded", model)
    return True


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
        workflow: Workflow | None = None,
    ) -> None:
        self.db_path = Path(db_path)
        self.files_dir = Path(files_dir)
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.logger = logger or get_logger(self.__class__.__name__)
        self.workflow = workflow or minimal_workflow

    async def ensure_ollama(self) -> bool:
        """Return ``True`` when Ollama and the desired model are available."""
        url = f"{self.base_url}/api/tags"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url)
        except Exception:  # noqa: BLE001
            self.logger.warning(
                "Ollama not reachable at %s. Install from https://ollama.com and start the service.",
                self.base_url,
            )
            return False
        tags = resp.json().get("models", [])
        if not tags:
            self.logger.warning(
                "No Ollama models installed. Attempting download of '%s'.",
                self.model,
            )
            return await pull_model(self.model, logger=self.logger)
        names = [m.get("name") for m in tags]
        if self.model not in names:
            self.logger.warning(
                "Model '%s' missing. Attempting download.",
                self.model,
            )
            return await pull_model(self.model, logger=self.logger)
        return True

    def setup_resources(self) -> None:
        """Create local resources if they do not exist."""
        if duckdb is None:
            self.logger.error(
                "DuckDB not installed. Run 'poetry install --with dev' to enable local storage."
            )
        elif not self.db_path.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
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
