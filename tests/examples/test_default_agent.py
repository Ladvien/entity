import os
import subprocess
import sys

import pytest

from entity.infrastructure.ollama_infra import OllamaInfrastructure

pytest.skip("Zero config agent output not deterministic", allow_module_level=True)


@pytest.mark.examples
def test_default_agent():
    ollama = OllamaInfrastructure(
        "http://localhost:11434",
        "llama3.2:3b",
    )
    if not ollama.health_check():
        pytest.skip("No LLM infrastructure available")

    # Set Ollama environment variable
    llm_url = ollama.base_url
    env_var = "ENTITY_OLLAMA_URL"

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
