import os
import subprocess
import sys
from pathlib import Path

import pytest


class TestExamples:
    """Ensure example scripts run without errors."""

    scripts = [
        Path("examples/advanced_llm.py"),
        Path("examples/pipelines/pipeline_example.py"),
    ]

    @pytest.mark.slow
    @pytest.mark.examples
    @pytest.mark.parametrize("script", scripts)
    def test_run(self, script: Path) -> None:
        if not os.environ.get("RUN_EXAMPLE_TESTS"):
            pytest.skip("RUN_EXAMPLE_TESTS not set")
        subprocess.run([sys.executable, str(script)], check=True)
