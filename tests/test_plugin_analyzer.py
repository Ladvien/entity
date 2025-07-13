import logging
from pathlib import Path

import pytest

from entity.pipeline import Plugin  # noqa: F401 - triggers plugin configuration
from entity.pipeline.initializer import SystemInitializer
from entity.pipeline.errors import InitializationError

from entity.core.decorators import plugin
from entity.core.stages import PipelineStage
from entity.core.plugins import (
    InfrastructurePlugin,
    PromptPlugin,
    ResourcePlugin,
)


class EmptyStagePrompt(PromptPlugin):
    stages: list = []

    async def _execute_impl(self, context):  # pragma: no cover - stub
        return None


class MissingInfraType(InfrastructurePlugin):
    stages: list = []
    dependencies: list = []

    async def _execute_impl(self, context):  # pragma: no cover - stub
        return None


class MissingDepsResource(ResourcePlugin):
    stages: list = []
    infrastructure_dependencies: list = []

    async def _execute_impl(self, context):  # pragma: no cover - stub
        return None


def test_warning_logged_for_complex_function(caplog):
    async def complex_func(context):
        total = 0
        for i in range(5):
            if i > 2:
                break
            total += i
        for j in range(3):
            total += j
        for k in range(3):
            total += k
        for l in range(3):
            total += l
        for m in range(3):
            total += m
        for n in range(3):
            total += n
        for o in range(3):
            total += o
        for p in range(3):
            total += p
        for q in range(3):
            total += q
        for r in range(3):
            total += r
        return total

    with caplog.at_level(logging.WARNING):
        plugin(stage=PipelineStage.THINK)(complex_func)

    assert any("consider" in record.message for record in caplog.records)


def test_discovered_prompt_requires_stages(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[tool.entity.plugins.prompts.bad]
type = "tests.test_plugin_analyzer:EmptyStagePrompt"
"""
    )
    initializer = SystemInitializer()
    initializer.config["plugin_dirs"] = [str(tmp_path)]
    with pytest.raises(InitializationError, match="stages"):
        initializer._discover_plugins()


def test_discovered_infra_requires_type(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[tool.entity.plugins.infrastructure.bad]
type = "tests.test_plugin_analyzer:MissingInfraType"
"""
    )
    initializer = SystemInitializer()
    initializer.config["plugin_dirs"] = [str(tmp_path)]
    with pytest.raises(InitializationError, match="infrastructure_type"):
        initializer._discover_plugins()


def test_discovered_resource_requires_dependencies(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[tool.entity.plugins.resources.bad]
type = "tests.test_plugin_analyzer:MissingDepsResource"
"""
    )
    initializer = SystemInitializer()
    initializer.config["plugin_dirs"] = [str(tmp_path)]
    with pytest.raises(InitializationError, match="infrastructure_dependencies"):
        initializer._discover_plugins()
