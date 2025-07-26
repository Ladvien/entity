from entity import defaults
from entity.defaults import load_defaults


class DummyVLLM:
    def __init__(self, *args, **kwargs):
        pass

    async def generate(self, prompt: str) -> str:
        return "vllm"

    def health_check(self) -> bool:
        return True


class FailingVLLM(DummyVLLM):
    def health_check(self) -> bool:
        return False


class DummyOllama:
    def __init__(self, *args, **kwargs):
        pass

    async def generate(self, prompt: str) -> str:
        return "ollama"

    def health_check(self) -> bool:
        return True


def test_vllm_preferred(monkeypatch):
    monkeypatch.setenv("ENTITY_AUTO_INSTALL_VLLM", "true")
    monkeypatch.setattr(defaults, "VLLMInfrastructure", lambda *a, **k: DummyVLLM())
    monkeypatch.setattr(defaults, "OllamaInfrastructure", lambda *a, **k: DummyOllama())
    monkeypatch.setattr(
        defaults.VLLMInstaller, "ensure_vllm_available", lambda *a, **k: None
    )
    monkeypatch.setattr(
        defaults.OllamaInstaller, "ensure_ollama_available", lambda *a, **k: None
    )

    resources = load_defaults()
    assert isinstance(resources["llm"].resource.infrastructure, DummyVLLM)


def test_vllm_fallback(monkeypatch):
    monkeypatch.setenv("ENTITY_AUTO_INSTALL_VLLM", "true")
    monkeypatch.setattr(defaults, "VLLMInfrastructure", lambda *a, **k: FailingVLLM())
    monkeypatch.setattr(defaults, "OllamaInfrastructure", lambda *a, **k: DummyOllama())
    monkeypatch.setattr(
        defaults.VLLMInstaller, "ensure_vllm_available", lambda *a, **k: None
    )
    monkeypatch.setattr(
        defaults.OllamaInstaller, "ensure_ollama_available", lambda *a, **k: None
    )

    resources = load_defaults()
    assert isinstance(resources["llm"].resource.infrastructure, DummyOllama)
