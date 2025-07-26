import types

from entity.defaults import load_defaults
from entity.setup.vllm_installer import VLLMInstaller
from entity.infrastructure.vllm_infra import VLLMInfrastructure
from entity.infrastructure.ollama_infra import OllamaInfrastructure


def test_load_defaults_prefers_vllm(monkeypatch):
    monkeypatch.setenv("ENTITY_AUTO_INSTALL_VLLM", "1")
    monkeypatch.setenv("ENTITY_AUTO_INSTALL_OLLAMA", "0")

    monkeypatch.setattr(VLLMInstaller, "ensure_vllm_available", lambda: None)
    monkeypatch.setattr(VLLMInfrastructure, "health_check", lambda self: True)

    resources = load_defaults()
    assert isinstance(resources["llm"].resource.infrastructure, VLLMInfrastructure)


def test_load_defaults_fallbacks_to_ollama(monkeypatch):
    monkeypatch.setenv("ENTITY_AUTO_INSTALL_VLLM", "1")
    monkeypatch.setenv("ENTITY_AUTO_INSTALL_OLLAMA", "1")

    monkeypatch.setattr(VLLMInstaller, "ensure_vllm_available", lambda: None)
    monkeypatch.setattr(VLLMInfrastructure, "health_check", lambda self: False)
    monkeypatch.setattr(OllamaInfrastructure, "health_check", lambda self: True)

    resources = load_defaults()
    assert isinstance(resources["llm"].resource.infrastructure, OllamaInfrastructure)
