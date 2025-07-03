import sys
from pathlib import Path

import pytest

from config.environment import load_env

SRC_PATH = str(Path(__file__).resolve().parents[1] / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)


@pytest.fixture(autouse=True)
def _load_test_env():
    """Load environment variables for tests."""
    env_path = Path(__file__).resolve().parents[1] / ".env"
    load_env(env_path)
    yield
