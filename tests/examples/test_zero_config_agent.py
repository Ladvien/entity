import os
import subprocess
import sys

import pytest


@pytest.mark.examples
def test_zero_config_agent():
    env = dict(os.environ, PYTHONPATH="src")
    proc = subprocess.run(
        [sys.executable, "examples/zero_config_agent.py"],
        input="ping\n",
        text=True,
        capture_output=True,
        timeout=5,
        env=env,
    )
    assert proc.stdout.strip() == "ping"
