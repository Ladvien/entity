from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


def _load_env_file(path: Path) -> None:
    """Load variables from ``path`` if it exists."""
    if path.exists():
        load_dotenv(path)


def load_env(env_file: str | Path = ".env") -> None:
    """Load variables from a file, falling back to ``.env.example``.

    Environment variables already set are not overwritten.
    """
    env_path = Path(env_file)
    _load_env_file(env_path)
    if not env_path.exists() and env_path.name == ".env":
        example_path = env_path.with_name(".env.example")
        _load_env_file(example_path)
