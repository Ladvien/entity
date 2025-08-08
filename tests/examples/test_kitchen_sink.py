import os
import sys

import asyncio
import pytest

from entity.infrastructure.vllm_infra import VLLMInfrastructure
from entity.infrastructure.ollama_infra import OllamaInfrastructure


@pytest.mark.examples
def test_kitchen_sink(capsys):
    vllm = VLLMInfrastructure()
    ollama = OllamaInfrastructure(
        "http://localhost:11434",
        "llama3.2:3b",
    )
    if not vllm.health_check_sync() and not ollama.health_check_sync():
        pytest.skip("No LLM infrastructure available")

    # Determine which LLM is available and set the appropriate environment variable
    llm_url = None
    if vllm.health_check_sync():
        llm_url = vllm.base_url
        os.environ["ENTITY_VLLM_URL"] = llm_url
    elif ollama.health_check_sync():
        llm_url = ollama.base_url
        os.environ["ENTITY_OLLAMA_URL"] = llm_url
    else:
        pytest.skip("No LLM infrastructure available")

    sys.path.insert(0, "src")
    import examples.kitchen_sink as ks

    pytest.skip("Output varies with real LLM", allow_module_level=False)
