"""Auto deploy AWS Bedrock infrastructure.

Run with ``python -m examples.bedrock_deploy`` or install the package in
editable mode.
"""

from __future__ import annotations

import os


from .utilities import enable_plugins_namespace

enable_plugins_namespace()


def deploy() -> None:
    """Placeholder deploy function."""

    print("Bedrock deployment requires optional infrastructure modules")


def can_deploy() -> bool:
    """Return ``True`` if required AWS credentials are present."""

    return bool(os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"))


if __name__ == "__main__":  # pragma: no cover - manual example
    if not can_deploy():
        print("AWS credentials not configured")
    else:
        try:
            deploy()
        except FileNotFoundError as exc:
            print(f"cdktf not available: {exc}")
