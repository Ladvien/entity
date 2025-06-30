from pathlib import Path

import pytest

from config.environment import load_env


@pytest.fixture(autouse=True)
def _load_test_env(monkeypatch):
    """Load environment variables for tests from the .env file."""
    env_path = Path(__file__).resolve().parents[1] / ".env"
    load_env(env_path)
    yield
