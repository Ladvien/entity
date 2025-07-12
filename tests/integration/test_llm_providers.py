import pytest
from plugins.builtin.resources.llm.unified import UnifiedLLMResource

PROVIDER_CONFIGS = {
    "openai": {
        "provider": "openai",
        "api_key": "key",
        "model": "model",
        "base_url": "http://localhost",
    },
    "ollama": {
        "provider": "ollama",
        "model": "model",
        "base_url": "http://localhost",
    },
    "gemini": {
        "provider": "gemini",
        "api_key": "key",
        "model": "model",
        "base_url": "http://localhost",
    },
    "claude": {
        "provider": "claude",
        "api_key": "key",
        "model": "model",
        "base_url": "http://localhost",
    },
    "bedrock": {"provider": "bedrock", "model_id": "model"},
    "echo": {"provider": "echo"},
}


@pytest.mark.integration
@pytest.mark.parametrize("provider,cfg", PROVIDER_CONFIGS.items())
def test_unified_llm_provider_initialization(provider: str, cfg: dict) -> None:
    resource = UnifiedLLMResource(cfg)
    assert resource._providers[0].name == provider
