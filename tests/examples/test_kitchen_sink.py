import os
import sys

import asyncio
import pytest

from entity.infrastructure.vllm_infra import VLLMInfrastructure
from entity.infrastructure.ollama_infra import OllamaInfrastructure


def _get_llm_url() -> str | None:
    vllm = VLLMInfrastructure(auto_install=False)
    if vllm.health_check():
        return vllm.base_url
    ollama = OllamaInfrastructure(
        "http://localhost:11434",
        "llama3.2:3b",
        auto_install=False,
    )
    if ollama.health_check():
        return ollama.base_url
    return None


if _get_llm_url() is None:
    pytest.skip("No LLM infrastructure available", allow_module_level=True)


@pytest.mark.examples
def test_kitchen_sink(capsys):
    llm_url = _get_llm_url()
    if llm_url is None:
        pytest.skip("No LLM infrastructure available")
    os.environ["ENTITY_OLLAMA_URL"] = llm_url
    sys.path.insert(0, "src")
    import examples.kitchen_sink as ks

    pytest.skip("Output varies with real LLM", allow_module_level=False)
