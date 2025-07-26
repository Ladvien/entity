import builtins

import pytest

from entity.defaults import load_defaults
from entity.setup.ollama_installer import OllamaInstaller


def test_auto_install_enabled(monkeypatch):
    calls = []

    def fake_install(model=None):
        calls.append(model)

    monkeypatch.setenv("ENTITY_AUTO_INSTALL_OLLAMA", "true")
    monkeypatch.setattr(OllamaInstaller, "ensure_ollama_available", fake_install)

    load_defaults()

    assert calls


def test_auto_install_disabled(monkeypatch):
    called = False

    def fake_install(model=None):
        nonlocal called
        called = True

    monkeypatch.setenv("ENTITY_AUTO_INSTALL_OLLAMA", "false")
    monkeypatch.setattr(OllamaInstaller, "ensure_ollama_available", fake_install)

    load_defaults()

    assert not called
