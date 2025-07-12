import subprocess

import pytest

EXAMPLES = [
    "examples/basic_agent/main.py",
    "examples/intermediate_agent/main.py",
    "examples/advanced_agent/main.py",
]


@pytest.mark.examples
@pytest.mark.parametrize("script", EXAMPLES)
def test_example_runs(script):
    result = subprocess.run(
        ["poetry", "run", "python", script],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
