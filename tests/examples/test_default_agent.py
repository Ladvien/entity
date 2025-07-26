import os
import subprocess
import sys

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
pytest.skip("Zero config agent output not deterministic", allow_module_level=True)


@pytest.mark.examples
def test_default_agent():
    url = _get_llm_url()
    if url is None:
        pytest.skip("No LLM infrastructure available")
    env = dict(os.environ, PYTHONPATH="src", ENTITY_OLLAMA_URL=url)
    proc = subprocess.run(
        [sys.executable, "examples/default_agent.py"],
        input="ping\n",
        text=True,
        capture_output=True,
        timeout=5,
        env=env,
    )
    assert proc.stdout.strip()
