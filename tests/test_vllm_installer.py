import importlib

import pytest

from entity.setup.vllm_installer import VLLMInstaller


def test_vllm_installed(monkeypatch):
    monkeypatch.setattr(importlib, "import_module", lambda name: object())
    VLLMInstaller.ensure_vllm_available()


def test_vllm_missing(monkeypatch, caplog):
    def _raise(name):
        raise ModuleNotFoundError

    monkeypatch.setattr(importlib, "import_module", _raise)
    caplog.set_level("WARNING")
    VLLMInstaller.ensure_vllm_available()
    assert "not installed" in caplog.text
