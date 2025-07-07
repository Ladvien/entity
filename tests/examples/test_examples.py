import os
import subprocess
import sys
from importlib import import_module
from pathlib import Path

import pytest

from plugins.builtin.infrastructure import infrastructure

if not infrastructure.CDKTF_AVAILABLE:  # pragma: no cover - optional dependency
    pytest.skip("cdktf not available", allow_module_level=True)

from pipeline import SystemRegistries


def test_pipeline_example_setup_registries() -> None:
    mod = import_module("examples.pipelines.pipeline_example")
    regs = mod.setup_registries()
    assert isinstance(regs, SystemRegistries)


def test_example_modules_importable() -> None:
    modules = [
        "examples.advanced_llm",
        "examples.bedrock_deploy",
        "examples.servers.http_server",
        "examples.utilities.plugin_loader",
        "examples.pipelines.memory_composition_pipeline",
        "examples.pipelines.vector_memory_pipeline",
        "examples.pipelines.duckdb_pipeline",
    ]
    for name in modules:
        import_module(name)


class TestExamples:
    """Ensure example scripts run without errors."""

    scripts = [
        Path("examples/advanced_llm.py"),
        Path("examples/pipelines/pipeline_example.py"),
        Path("examples/pipelines/duckdb_pipeline.py"),
        Path("examples/pipelines/memory_composition_pipeline.py"),
        Path("examples/pipelines/vector_memory_pipeline.py"),
    ]

    @pytest.mark.slow
    @pytest.mark.examples
    @pytest.mark.parametrize("script", scripts)
    def test_run(self, script: Path) -> None:
        if not os.environ.get("RUN_EXAMPLE_TESTS"):
            pytest.skip("RUN_EXAMPLE_TESTS not set")
        subprocess.run([sys.executable, str(script)], check=True)
