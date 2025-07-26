import os
import subprocess
import sys

import pytest

from entity.infrastructure.vllm_infra import VLLMInfrastructure
from entity.infrastructure.ollama_infra import OllamaInfrastructure


pytest.skip("Zero config agent output not deterministic", allow_module_level=True)


@pytest.mark.examples
def test_default_agent():
    vllm = VLLMInfrastructure()
    ollama = OllamaInfrastructure(
        "http://localhost:11434",
        "llama3.2:3b",
    )
    if not vllm.health_check() and not ollama.health_check():
        pytest.skip("No LLM infrastructure available")

    # Determine which LLM is available and set the appropriate environment variable
    llm_url = None
    if vllm.health_check():
        llm_url = vllm.base_url
        env_var = "ENTITY_VLLM_URL"
    elif ollama.health_check():
        llm_url = ollama.base_url
        env_var = "ENTITY_OLLAMA_URL"
    else:
        pytest.skip("No LLM infrastructure available")

    env = dict(os.environ, PYTHONPATH="src", **{env_var: llm_url})
    proc = subprocess.run(
        [sys.executable, "examples/default_agent.py"],
        input="ping\n",
        text=True,
        capture_output=True,
        timeout=5,
        env=env,
    )
    assert proc.stdout.strip()
