import os
import subprocess
import sys

from tests.fixtures.local_resources import mock_ollama_server
import pytest


@pytest.mark.examples
def test_zero_config_agent(mock_ollama_server):
    env = dict(
        os.environ,
        PYTHONPATH="src",
        ENTITY_OLLAMA_URL=mock_ollama_server,
    )
    proc = subprocess.run(
        [sys.executable, "examples/zero_config_agent.py"],
        input="ping\n",
        text=True,
        capture_output=True,
        timeout=5,
        env=env,
    )
    assert proc.stdout.strip() == "ping"
