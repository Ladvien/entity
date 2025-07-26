import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.fixtures.local_resources import mock_ollama_server


@pytest.mark.integration
def test_cli_help(mock_ollama_server):
    env = dict(os.environ, ENTITY_OLLAMA_URL=mock_ollama_server)
    result = subprocess.run(
        [sys.executable, "-m", "entity.cli", "--help"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert "workflow" in result.stdout.lower()


@pytest.mark.integration
def test_cli_default_workflow(mock_ollama_server):
    env = dict(os.environ, ENTITY_OLLAMA_URL=mock_ollama_server)
    proc = subprocess.run(
        [sys.executable, "-m", "entity.cli", "--workflow", "default"],
        input="hello\n",
        capture_output=True,
        text=True,
        timeout=5,
        env=env,
    )
    assert proc.stdout.strip() == "hello"


@pytest.mark.integration
def test_cli_verbose_flag(mock_ollama_server):
    env = dict(os.environ, ENTITY_OLLAMA_URL=mock_ollama_server)
    proc = subprocess.run(
        [sys.executable, "-m", "entity.cli", "--workflow", "default", "--verbose"],
        input="hi\n",
        capture_output=True,
        text=True,
        timeout=5,
        env=env,
    )
    assert proc.stdout.strip() == "hi"


@pytest.mark.integration
def test_cli_custom_workflow(mock_ollama_server):
    workflow_file = Path("tests/data/simple_workflow.yaml")
    env = dict(os.environ, ENTITY_OLLAMA_URL=mock_ollama_server)
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
    assert proc.stdout.strip() == "ping"


@pytest.mark.integration
def test_cli_unknown_workflow():
    proc = subprocess.run(
        [sys.executable, "-m", "entity.cli", "--workflow", "missing"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert "not found" in proc.stderr.lower()
