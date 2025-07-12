"""Environment helpers for Entity."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values


def load_env(env_file: str | Path = ".env", env: str | None = None) -> None:
    """Load variables from ``env_file`` and ``secrets/<env>.env``.

    Existing process variables are never overwritten. Values from
    ``secrets/<env>.env`` override entries from ``env_file`` when both
    are present.
    """

    env_values = {}

    env_path = Path(env_file)
    if env_path.exists():
        env_values.update(dotenv_values(env_path))

    env_name = env or os.getenv("ENTITY_ENV")
    if env_name:
        secret_path = Path("secrets") / f"{env_name}.env"
        if secret_path.exists():
            env_values.update(dotenv_values(secret_path))

    for key, value in env_values.items():
        os.environ.setdefault(key, value)
