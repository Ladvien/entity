from __future__ import annotations

"""Environment loading utilities used in tests."""

from pathlib import Path
from typing import Any

from dotenv import load_dotenv


def load_env(env_file: str | Path = ".env", override: bool = False) -> None:
    """Load environment variables from ``env_file``."""
    path = Path(env_file)
    if path.exists():
        load_dotenv(path, override=override)
