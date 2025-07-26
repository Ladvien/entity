import os
import subprocess
import sys

import pytest


@pytest.mark.examples
def test_advanced_workflow():
    env = dict(os.environ, PYTHONPATH="src", ENTITY_AUTO_INSTALL_OLLAMA="false")
    proc = subprocess.run(
        [sys.executable, "examples/advanced_workflow.py"],
        capture_output=True,
        text=True,
        timeout=5,
        env=env,
    )
    assert proc.stdout.strip() == "Result: 4"
