import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parent))
from fixtures.local_resources import (
    local_duckdb_path,
    local_storage_dir,
    mock_ollama_server,
)

ENTITY_TEST_MODE = os.getenv("ENTITY_TEST_MODE", "local")

COMPOSE_FILE = Path(__file__).resolve().parents[1] / "docker-compose.yml"


def _compose(*args: str) -> None:
    subprocess.check_call(["docker", "compose", "-f", str(COMPOSE_FILE), *args])


@pytest.fixture(scope="session")
def compose_services():
    """Start docker-compose services for integration tests."""
    if shutil.which("docker") is None:
        pytest.skip("docker not installed")
    _compose("up", "-d")
    try:
        yield
    finally:
        _compose("down", "-v")


def pytest_collection_modifyitems(config, items):
    for item in items:
        if "docker" in item.keywords:
            item.fixturenames.append("compose_services")
        elif ENTITY_TEST_MODE == "docker" and "integration" in item.keywords:
            item.fixturenames.append("compose_services")
