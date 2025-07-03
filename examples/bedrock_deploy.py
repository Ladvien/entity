"""Auto deploy AWS Bedrock infrastructure."""

from __future__ import annotations

import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from infrastructure.aws_bedrock import deploy

if __name__ == "__main__":  # pragma: no cover - manual example
    deploy()
