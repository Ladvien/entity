import asyncio
import os
import sys

import pytest


@pytest.mark.examples
@pytest.mark.asyncio
async def test_advanced_workflow(monkeypatch, capsys):
    monkeypatch.setattr(
        "entity.setup.ollama_installer.OllamaInstaller.ensure_ollama_available",
        lambda model=None: None,
    )
    monkeypatch.setattr(
        "entity.infrastructure.ollama_infra.OllamaInfrastructure.health_check",
        lambda self: False,
    )
    sys.path.insert(0, "src")
    sys.path.insert(0, ".")
    import importlib

    mod = importlib.import_module("examples.advanced_workflow")
    await mod.main()
    captured = capsys.readouterr()
    assert captured.out.strip().endswith("Result: 4")
