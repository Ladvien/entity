import pytest

from entity.defaults import load_defaults
from entity.infrastructure.ollama_infra import OllamaInfrastructure
from entity.infrastructure.vllm_infra import VLLMInfrastructure


def _available_infra():
    vllm = VLLMInfrastructure()
    if vllm.health_check():
        return vllm
    ollama = OllamaInfrastructure("http://localhost:11434", "llama3.2:3b")
    if ollama.health_check():
        return ollama
    return None


@pytest.mark.integration
@pytest.mark.requires_ollama
def test_load_defaults_uses_available_llm():
    infra = _available_infra()
    if infra is None:
        pytest.skip("No LLM infrastructure available")
    resources = load_defaults()
    assert resources["llm"].resource.infrastructure.__class__ is infra.__class__
