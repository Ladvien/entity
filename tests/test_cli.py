import os
import subprocess
import sys
from pathlib import Path

import pytest

from entity.infrastructure.vllm_infra import VLLMInfrastructure
from entity.infrastructure.ollama_infra import OllamaInfrastructure


pytest.skip("CLI integration requires deterministic LLM", allow_module_level=True)


@pytest.mark.integration
def test_cli_help():
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

    env = dict(os.environ, **{env_var: llm_url})
    result = subprocess.run(
        [sys.executable, "-m", "entity.cli", "--help"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert "workflow" in result.stdout.lower()


@pytest.mark.integration
def test_cli_default_workflow():
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

    env = dict(os.environ, **{env_var: llm_url})
    proc = subprocess.run(
        [sys.executable, "-m", "entity.cli", "--workflow", "default"],
        input="hello\n",
        capture_output=True,
        text=True,
        timeout=5,
        env=env,
    )
    assert proc.stdout.strip()


@pytest.mark.integration
def test_cli_verbose_flag():
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

    env = dict(os.environ, **{env_var: llm_url})
    proc = subprocess.run(
        [sys.executable, "-m", "entity.cli", "--workflow", "default", "--verbose"],
        input="hi\n",
        capture_output=True,
        text=True,
        timeout=5,
        env=env,
    )
    assert proc.stdout.strip()


@pytest.mark.integration
def test_cli_custom_workflow():
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

    workflow_file = Path("tests/data/simple_workflow.yaml")
    env = dict(os.environ, **{env_var: llm_url})
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "entity.cli",
            "--workflow",
            str(workflow_file),
        ],
        input="ping\n",
        capture_output=True,
        text=True,
        timeout=5,
        env=env,
    )
    assert proc.stdout.strip()


@pytest.mark.integration
def test_cli_unknown_workflow():
    proc = subprocess.run(
        [sys.executable, "-m", "entity.cli", "--workflow", "missing"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert "not found" in proc.stderr.lower()