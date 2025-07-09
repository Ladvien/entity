import subprocess
import sys

import yaml


def _write_config(path, value=True, tool=False, include_plugin=True):
    cfg = {"plugins": {"prompts": {}}}
    if include_plugin:
        cfg["plugins"]["prompts"]["reload"] = {
            "type": "user_plugins.test_plugins:ReloadPlugin"
        }
    if include_plugin and value is not False:
        cfg["plugins"]["prompts"]["reload"]["value"] = value
    if tool:
        cfg["plugins"].setdefault("tools", {})["echo"] = {
            "type": "user_plugins.test_plugins:ReloadTool"
        }
    path.write_text(yaml.dump(cfg, sort_keys=False))


def test_cli_reload_success(tmp_path):
    base = tmp_path / "base.yml"
    update = tmp_path / "update.yml"
    _write_config(base, value="one")
    _write_config(update, value="two")

    result = subprocess.run(
        [
            sys.executable,
            "src/cli.py",
            "--config",
            str(base),
            "reload-config",
            str(update),
        ],
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0


def test_cli_reload_failure(tmp_path):
    base = tmp_path / "base.yml"
    bad = tmp_path / "bad.yml"
    _write_config(base, value="one")
    _write_config(bad, value=False)

    result = subprocess.run(
        [
            sys.executable,
            "src/cli.py",
            "--config",
            str(base),
            "reload-config",
            str(bad),
        ],
        text=True,
        capture_output=True,
    )
    assert result.returncode != 0
    assert "Failed to update" in result.stderr


def test_cli_reload_add_tool(tmp_path):
    base = tmp_path / "base.yml"
    update = tmp_path / "update.yml"
    _write_config(base, value="one")
    _write_config(update, value="two", tool=True)

    result = subprocess.run(
        [
            sys.executable,
            "src/cli.py",
            "--config",
            str(base),
            "reload-config",
            str(update),
        ],
        text=True,
        capture_output=True,
    )
    assert result.returncode != 0


def test_cli_reload_remove_plugin(tmp_path):
    base = tmp_path / "base.yml"
    update = tmp_path / "update.yml"
    _write_config(base, value="one")
    _write_config(update, include_plugin=False)

    result = subprocess.run(
        [
            sys.executable,
            "src/cli.py",
            "--config",
            str(base),
            "reload-config",
            str(update),
        ],
        text=True,
        capture_output=True,
    )
    assert result.returncode != 0
