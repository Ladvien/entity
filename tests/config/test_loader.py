import os
from pathlib import Path

from entity.config.environment import load_config


def test_load_config_interpolates(monkeypatch, tmp_path):
    cfg = tmp_path / "base.yaml"
    cfg.write_text("path: ${TEST_DIR}/data\n")
    monkeypatch.setenv("TEST_DIR", "/tmp")

    result = load_config(cfg)

    assert result["path"] == "/tmp/data"


def test_load_config_with_overlay(monkeypatch, tmp_path):
    base = tmp_path / "base.yaml"
    base.write_text("foo: ${VAR}\n")
    overlay = tmp_path / "override.yaml"
    overlay.write_text("foo: bar\n")
    monkeypatch.setenv("VAR", "baz")

    result = load_config(base, overlay)

    assert result["foo"] == "bar"
