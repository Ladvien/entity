import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def configure_ollama():
    os.environ.setdefault("ENTITY_AUTO_INSTALL_OLLAMA", "1")
    os.environ.setdefault("ENTITY_AUTO_INSTALL_VLLM", "0")
    yield
