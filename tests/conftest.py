import pytest
import os


def is_ollama_key_available():
    """Check if the Ollama key is available."""
    return os.path.exists(os.path.expanduser("~/.ollama/id_ed25519"))


def pytest_configure(config):
    """Register the 'requires_ollama' marker."""
    config.addinivalue_line(
        "markers", "requires_ollama: mark test as requiring ollama to be configured"
    )


def pytest_collection_modifyitems(config, items):
    """Skip tests marked with 'requires_ollama' if the key is not available."""
    if not is_ollama_key_available():
        skip_ollama = pytest.mark.skip(
            reason="Ollama key not found. Run 'ollama login' and try again."
        )
        for item in items:
            if "requires_ollama" in item.keywords:
                item.add_marker(skip_ollama)
