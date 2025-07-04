import sys
from pathlib import Path

SRC_PATH = Path(__file__).resolve().parents[1]
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from .builder import ConfigBuilder  # noqa: E402

__all__ = ["ConfigBuilder"]
