import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.integration
def test_cli_help():
    result = subprocess.run(
        [sys.executable, "-m", "entity.cli", "--help"],
        capture_output=True,
        text=True,
    )
    assert "workflow" in result.stdout.lower()


@pytest.mark.integration
def test_cli_default_workflow():
    proc = subprocess.run(
        [sys.executable, "-m", "entity.cli", "--workflow", "default"],
        input="hello\n",
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert proc.stdout.strip() == "hello"


@pytest.mark.integration
def test_cli_verbose_flag():
    proc = subprocess.run(
        [sys.executable, "-m", "entity.cli", "--workflow", "default", "--verbose"],
        input="hi\n",
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert proc.stdout.strip() == "hi"


@pytest.mark.integration
def test_cli_custom_workflow(tmp_path):
    workflow_file = Path("tests/data/simple_workflow.yaml")
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


# TODO: Timeout functionality removed - not part of MVP scope
