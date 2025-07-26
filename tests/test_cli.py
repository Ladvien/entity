import os
import subprocess
import sys
from pathlib import Path

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
pytest.skip("CLI integration requires deterministic LLM", allow_module_level=True)


if _get_llm_url() is None:
    pytest.skip("No LLM infrastructure available", allow_module_level=True)


@pytest.mark.integration
def test_cli_help():
    url = _get_llm_url()
    if url is None:
        pytest.skip("No LLM infrastructure available")
    env = dict(os.environ, ENTITY_OLLAMA_URL=url)
    result = subprocess.run(
        [sys.executable, "-m", "entity.cli", "--help"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert "workflow" in result.stdout.lower()


@pytest.mark.integration
def test_cli_default_workflow():
    url = _get_llm_url()
    if url is None:
        pytest.skip("No LLM infrastructure available")
    env = dict(os.environ, ENTITY_OLLAMA_URL=url)
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
    url = _get_llm_url()
    if url is None:
        pytest.skip("No LLM infrastructure available")
    env = dict(os.environ, ENTITY_OLLAMA_URL=url)
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
    url = _get_llm_url()
    if url is None:
        pytest.skip("No LLM infrastructure available")
    workflow_file = Path("tests/data/simple_workflow.yaml")
    env = dict(os.environ, ENTITY_OLLAMA_URL=url)
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
