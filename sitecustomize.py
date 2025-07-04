"""Ensure the repository's ``src`` directory is on ``sys.path``."""

from __future__ import annotations

import pathlib
import sys

SRC_PATH = pathlib.Path(__file__).resolve().parent / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))
