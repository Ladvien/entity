"""Ensure the repository's ``src`` directory is on ``sys.path``."""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
SRC_PATH = ROOT / "src"
GRPC_PATH = SRC_PATH / "grpc_services"

for path in (SRC_PATH, GRPC_PATH):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
