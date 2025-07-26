import os
from unittest.mock import patch

import pytest

from entity.setup import OllamaInstaller


@pytest.fixture(scope="session", autouse=True)
def configure_ollama():
    os.environ.setdefault("ENTITY_AUTO_INSTALL_OLLAMA", "1")
    with patch.object(
        OllamaInstaller, "ensure_ollama_available", lambda *_, **__: None
    ):
        yield
