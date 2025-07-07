"""Auto deploy AWS Bedrock infrastructure."""

from __future__ import annotations

import os
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from .utilities import enable_plugins_namespace

enable_plugins_namespace()

try:  # optional dependency
    from plugins.builtin.infrastructure.aws_bedrock import deploy
except (ImportError, FileNotFoundError):  # noqa: WPS440

    def deploy() -> None:
        """Fallback when CDKTF is unavailable."""

        return None


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
